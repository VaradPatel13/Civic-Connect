import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.deps import get_auth_service, get_current_user, get_user_repository
from backend.core.config import settings
from backend.models.base import PreferredLanguage, UserRole
from backend.models.citizens import Citizen
from backend.repositories.user import UserRepository
from backend.schemas.auth import (
    CitizenProfileResponse,
    LoginRequest,
    OTPVerifyRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from backend.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])



@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Registers a new citizen account and returns access/refresh tokens."""
    existing_phone = await user_repo.get_by_phone(payload.phone)
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A citizen with this phone number already exists.",
        )

    if payload.email:
        existing_email = await user_repo.get_by_email(payload.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A citizen with this email address already exists.",
            )

    try:
        lang_enum = PreferredLanguage(payload.preferred_language)
    except ValueError:
        lang_enum = PreferredLanguage.EN

    password_hash = auth_service.hash_password(payload.password)
    citizen = await user_repo.create(
        display_name=payload.display_name,
        phone=payload.phone,
        email=payload.email,
        password_hash=password_hash,
        preferred_language=lang_enum,
        role=UserRole.CITIZEN,
        is_active=True,
        is_verified=False,
    )

    # Generate initial OTP for newly registered citizen
    otp_code = auth_service.generate_otp()
    otp_hash = auth_service.hash_otp(otp_code)
    await user_repo.create_otp(
        citizen_id=citizen.id,
        phone=citizen.phone,
        code_hash=otp_hash,
        purpose="register",
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )

    otp_log = f"\n========================================\n🔑 [DEV OTP CODE] Registered Phone: {citizen.phone} | OTP: {otp_code}\n========================================\n"
    print(otp_log, flush=True)
    logger.info("🔑 [DEV OTP CODE] Registered Phone: %s | OTP: %s", citizen.phone, otp_code)

    role_str = str(citizen.role.value) if hasattr(citizen.role, "value") else str(citizen.role)
    access_token = auth_service.create_access_token(str(citizen.id), role=role_str)
    refresh_token = auth_service.create_refresh_token(str(citizen.id))

    refresh_hash = auth_service.hash_otp(refresh_token)
    await user_repo.create_session(
        citizen_id=citizen.id,
        refresh_token_hash=refresh_hash,
    )

    user_profile = auth_service.build_profile_response(citizen)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=user_profile,
    )


@router.post("/request-otp")
async def request_otp(
    phone: str,
    purpose: str = "register",
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Generates, logs to console, and stores OTP for a phone number."""
    otp_code = auth_service.generate_otp()
    otp_hash = auth_service.hash_otp(otp_code)
    expires_at = datetime.now(UTC) + timedelta(minutes=10)

    await user_repo.create_otp(
        phone=phone,
        code_hash=otp_hash,
        purpose=purpose,
        expires_at=expires_at,
    )

    otp_log = f"\n========================================\n🔑 [DEV OTP CODE] Phone: {phone} | OTP: {otp_code}\n========================================\n"
    print(otp_log, flush=True)
    logger.info("🔑 [DEV OTP CODE] Phone: %s | OTP: %s", phone, otp_code)

    return {
        "message": f"OTP generated and sent for {phone}",
        "otp": otp_code if settings.debug else None,
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticates a citizen with phone number and password."""
    citizen = await user_repo.get_by_phone(payload.phone)
    if not citizen or not auth_service.verify_password(payload.password, citizen.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid mobile number or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not citizen.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support.",
        )

    role_str = str(citizen.role.value) if hasattr(citizen.role, "value") else str(citizen.role)
    access_token = auth_service.create_access_token(str(citizen.id), role=role_str)
    refresh_token = auth_service.create_refresh_token(str(citizen.id))

    refresh_hash = auth_service.hash_otp(refresh_token)
    await user_repo.create_session(
        citizen_id=citizen.id,
        refresh_token_hash=refresh_hash,
    )

    user_profile = auth_service.build_profile_response(citizen)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=user_profile,
    )


@router.get("/me", response_model=CitizenProfileResponse)
async def get_me(
    current_user: Citizen = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> CitizenProfileResponse:
    """Returns profile for the currently authenticated user."""
    return auth_service.build_profile_response(current_user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Refreshes access and refresh tokens using a valid refresh token with Refresh Token Rotation."""
    decoded = auth_service.verify_token(payload.refresh_token, token_type="refresh")
    if not decoded or not decoded.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    try:
        citizen_id = uuid.UUID(decoded["sub"])
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in refresh token",
        ) from err

    # Verify that this refresh token exists and is active in the database session
    old_refresh_hash = auth_service.hash_otp(payload.refresh_token)
    active_session = await user_repo.get_active_session_by_hash(citizen_id, old_refresh_hash)
    if not active_session:
        # Replay attack detection or revoked token!
        # Security best practice: revoke all sessions for this user if token reuse/replay is detected
        await user_repo.revoke_all_sessions(citizen_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is revoked or invalid. Session terminated.",
        )

    citizen = await user_repo.get_by_id(citizen_id)
    if not citizen or not citizen.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or inactive",
        )

    # Invalidate (revoke) old refresh token session - Refresh Token Rotation (RTR)
    await user_repo.revoke_session(active_session.id)

    # Issue new access token and new rotated refresh token
    role_str = str(citizen.role.value) if hasattr(citizen.role, "value") else str(citizen.role)
    new_access_token = auth_service.create_access_token(str(citizen.id), role=role_str)
    new_refresh_token = auth_service.create_refresh_token(str(citizen.id))

    new_refresh_hash = auth_service.hash_otp(new_refresh_token)
    await user_repo.create_session(
        citizen_id=citizen.id,
        refresh_token_hash=new_refresh_hash,
    )

    user_profile = auth_service.build_profile_response(citizen)
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=user_profile,
    )


@router.post("/logout")
async def logout(
    payload: RefreshRequest | None = None,
    current_user: Citizen = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """Revokes active refresh token session and logs out user."""
    if payload and payload.refresh_token:
        refresh_hash = auth_service.hash_otp(payload.refresh_token)
        await user_repo.revoke_session_by_hash(refresh_hash)
    await user_repo.revoke_all_sessions(current_user.id)
    return {"message": "Logged out successfully"}


@router.post("/verify-otp")
async def verify_otp(
    payload: OTPVerifyRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Verifies OTP code for registration or password reset."""
    latest_otp = await user_repo.get_latest_otp(payload.phone, purpose=payload.purpose)

    # Check provided code against hashed code or dev mode wildcard
    provided_hash = auth_service.hash_otp(payload.code)
    valid_code = (
        (latest_otp and latest_otp.code_hash == provided_hash)
        or (settings.debug and payload.code in ("123456", "000000"))
    )

    if not valid_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code.",
        )

    otp_log = f"\n========================================\n✅ [DEV OTP VERIFIED] Phone: {payload.phone} | Code: {payload.code}\n========================================\n"
    print(otp_log, flush=True)
    logger.info("✅ [DEV OTP VERIFIED] Phone: %s | Code: %s", payload.phone, payload.code)

    return {"verified": True, "message": "OTP verified successfully."}

