from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import logging
import secrets
from typing import Annotated
import uuid

from cloudinary.exceptions import Error as CloudinaryError
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from pydantic import BaseModel

from backend.api.deps import get_current_user
from backend.core.config import settings
from backend.models.citizens import Citizen
from backend.services.upload_service import UploadResult, upload_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/uploads", tags=["Uploads"])

# ── In-Memory Capture Challenge Registry (5-minute TTL) ─────────────────────────

_ACTIVE_CHALLENGES: dict[str, dict] = {}


def _clean_expired_challenges() -> None:
    """Evict expired capture challenges."""
    now = datetime.now(UTC)
    expired = [cid for cid, ch in _ACTIVE_CHALLENGES.items() if ch["expires_at"] < now]
    for cid in expired:
        _ACTIVE_CHALLENGES.pop(cid, None)


def _get_signing_secret() -> str:
    """Helper to retrieve primary server secret for HMAC signing."""
    sec = getattr(settings, "jwt_secret_key", None) or getattr(settings, "jwt_secret", None)
    if isinstance(sec, str) and sec.strip():
        return sec.strip()
    return "civicconnect_secret_key"


# ── Request / Response models ─────────────────────────────────────────────────

class ChallengeResponse(BaseModel):
    """Short-lived server-issued capture challenge token."""

    challenge_id: str
    nonce:        str
    issued_at:    str
    expires_at:   str
    signed_token: str


class UploadResponse(BaseModel):
    """Cloudinary asset details + server signed provenance returned after upload."""

    url:            str
    secure_url:     str
    public_id:      str
    format:         str
    width:          int | None = None
    height:         int | None = None
    bytes:          int = 0
    sha256_hash:    str | None = None
    hmac_signature: str | None = None
    capture_source: str = "gallery"
    challenge_id:   str | None = None

    @classmethod
    def from_result(
        cls,
        r: UploadResult,
        sha256_hash: str | None = None,
        hmac_signature: str | None = None,
        capture_source: str = "gallery",
        challenge_id: str | None = None,
    ) -> UploadResponse:
        return cls(
            url            = r.url,
            secure_url     = r.secure_url,
            public_id      = r.public_id,
            format         = r.format,
            width          = r.width,
            height         = r.height,
            bytes          = r.bytes,
            sha256_hash    = sha256_hash,
            hmac_signature = hmac_signature,
            capture_source = capture_source,
            challenge_id   = challenge_id,
        )


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/challenge",
    response_model=ChallengeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue camera capture challenge",
    description="Issue a short-lived (5-min) server capture challenge token prior to camera capture.",
)
@router.get(
    "/challenge",
    response_model=ChallengeResponse,
    summary="Issue camera capture challenge",
)
async def create_capture_challenge(
    current_user: Citizen = Depends(get_current_user),
) -> ChallengeResponse:
    """Generate a short-lived capture challenge bound to current authenticated user."""
    _clean_expired_challenges()

    challenge_id = f"chl_{uuid.uuid4().hex}"
    nonce = secrets.token_hex(16)
    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=5)

    secret = _get_signing_secret()
    payload = f"{challenge_id}:{nonce}:{current_user.id}:{expires_at.isoformat()}"
    signed_token = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()

    _ACTIVE_CHALLENGES[challenge_id] = {
        "challenge_id": challenge_id,
        "nonce": nonce,
        "citizen_id": str(current_user.id),
        "issued_at": issued_at,
        "expires_at": expires_at,
        "signed_token": signed_token,
        "consumed": False,
    }

    logger.info(f"[CaptureChallenge] Issued {challenge_id} for user {current_user.id}")

    return ChallengeResponse(
        challenge_id=challenge_id,
        nonce=nonce,
        issued_at=issued_at.isoformat(),
        expires_at=expires_at.isoformat(),
        signed_token=signed_token,
    )


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
@router.post(
    "/",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a media asset",
    description="Upload an image directly to Cloudinary. Accepts optional capture challenge for camera provenance signing.",
)
async def upload_asset(
    file: Annotated[UploadFile, File(description="Image file (max 10 MB)")],
    challenge_id: Annotated[str | None, Form(description="Server capture challenge ID")] = None,
    signed_token: Annotated[str | None, Form(description="Capture challenge token signature")] = None,
    x_challenge_id: Annotated[str | None, Header(alias="X-Capture-Challenge-Id")] = None,
    x_challenge_token: Annotated[str | None, Header(alias="X-Capture-Challenge-Token")] = None,
    current_user: Citizen = Depends(get_current_user),
) -> UploadResponse:
    """Receive a file from the mobile client, validate provenance challenge, sign SHA-256, and upload to Cloudinary."""
    eff_challenge_id = challenge_id or x_challenge_id
    eff_challenge_token = signed_token or x_challenge_token

    # ── Validate content type ─────────────────────────────────────────────────
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Accepted: JPEG, PNG, WebP, HEIC.",
        )

    # ── Validate file size (10 MB cap) ─────────────────────────────────────────
    MAX_BYTES = 10 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 10 MB limit.",
        )
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Empty file uploaded.",
        )

    # ── Compute SHA-256 of original file bytes ─────────────────────────────
    sha256_hash = hashlib.sha256(content).hexdigest()

    # ── Validate Server-Issued Capture Challenge ──────────────────────────────
    hmac_signature: str | None = None
    capture_source = "gallery"
    secret = _get_signing_secret()

    if eff_challenge_id:
        _clean_expired_challenges()
        ch = _ACTIVE_CHALLENGES.get(eff_challenge_id)
        if not ch:
            logger.warning(f"[Uploads] Invalid or expired capture challenge {eff_challenge_id}")
        elif ch["citizen_id"] != str(current_user.id):
            logger.warning(f"[Uploads] Challenge {eff_challenge_id} citizen mismatch")
        elif ch["expires_at"] < datetime.now(UTC):
            logger.warning(f"[Uploads] Challenge {eff_challenge_id} expired")
        else:
            # Valid challenge: consume and generate server cryptographic signature
            ch["consumed"] = True
            capture_source = "camera"
            # Server-signed HMAC over image SHA-256 digest
            hmac_signature = hmac.new(secret.encode("utf-8"), sha256_hash.encode("utf-8"), hashlib.sha256).hexdigest()
            logger.info(f"[Uploads] Sealed server provenance signature for challenge {eff_challenge_id} (hash={sha256_hash[:8]}...)")

    # ── Upload to Cloudinary ───────────────────────────────────────────────────
    if not settings.cloudinary_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Media upload is temporarily unavailable.",
        )

    try:
        filename = file.filename or "upload"
        result = await asyncio.to_thread(upload_file, content, filename)
        return UploadResponse.from_result(
            result,
            sha256_hash=sha256_hash,
            hmac_signature=hmac_signature,
            capture_source=capture_source,
            challenge_id=eff_challenge_id,
        )

    except RuntimeError as e:
        logger.warning("Upload service not configured: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Media upload service is not configured.",
        ) from e
    except CloudinaryError as e:
        logger.exception("Cloudinary upload failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cloudinary upload failed.",
        ) from e
    except Exception as e:
        logger.exception("Unexpected upload failure: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed.",
        ) from e


