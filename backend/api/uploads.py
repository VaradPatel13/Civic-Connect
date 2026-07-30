"""
Signed upload URL generation for direct Cloudinary uploads.

Instead of proxying file bytes through the API server, the mobile client
requests a signed upload preset and uploads directly to Cloudinary.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Annotated

from cloudinary.exceptions import Error as CloudinaryError
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from backend.api.deps import get_current_user
from backend.core.config import settings
from backend.models.citizens import Citizen
from backend.services.upload_service import UploadResult, upload_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/uploads", tags=["Uploads"])


# ── Request / Response models ─────────────────────────────────────────────────

class UploadResponse(BaseModel):
    """Cloudinary asset details returned after a successful upload."""

    url:        str
    secure_url: str
    public_id:  str
    format:     str
    width:      int | None = None
    height:     int | None = None
    bytes:      int = 0

    @classmethod
    def from_result(cls, r: UploadResult) -> UploadResponse:
        return cls(
            url        = r.url,
            secure_url = r.secure_url,
            public_id  = r.public_id,
            format     = r.format,
            width      = r.width,
            height     = r.height,
            bytes      = r.bytes,
        )


# ── Endpoints ────────────────────────────────────────────────────────────────

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
    description="Upload an image directly to Cloudinary. Accepted formats: JPEG, PNG, WebP, HEIC.",
)
async def upload_asset(
    file: Annotated[UploadFile, File(description="Image file (max 10 MB)")],
    current_user: Citizen = Depends(get_current_user),
) -> UploadResponse:

    """
    Receive a file from the mobile client and upload it to Cloudinary.

    For large files prefer the presigned URL flow (TODO: future enhancement),
    which streams bytes directly to Cloudinary without hitting this server.
    """
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

    # ── Upload to Cloudinary ───────────────────────────────────────────────────
    if not settings.cloudinary_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Media upload is temporarily unavailable.",
        )

    try:
        filename = file.filename or "upload"
        result = await asyncio.to_thread(upload_file, content, filename)
        return UploadResponse.from_result(result)

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

