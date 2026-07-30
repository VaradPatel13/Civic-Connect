import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

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


def _mask_phone(phone: str) -> str:
    """Masks phone number for secure logging (e.g., ******3210)."""
    if len(phone) >= 4:
        return "*" * (len(phone) - 4) + phone[-4:]
    return "****"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Registers a new citizen account and returns access/refresh tokens."""
    masked_phone = _mask_phone(payload.phone)
    logger.debug("Registration attempt for phone: %s", masked_phone)

    try:
        existing_phone = await user_repo.get_by_phone(payload.phone)
        if existing_phone:
            logger.warning("Registration failed: Phone number already exists (%s)", masked_phone)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A citizen with this phone number already exists.",
            )

        if payload.email:
            existing_email = await user_repo.get_by_email(payload.email)
            if existing_email:
                logger.warning("Registration failed: Email address already exists")
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

        if settings.debug:
            logger.info("🔑 [DEV OTP CODE] Registered Phone: %s | OTP: %s", citizen.phone, otp_code)

        role_str = str(citizen.role.value) if hasattr(citizen.role, "value") else str(citizen.role)
        access_token = auth_service.create_access_token(str(citizen.id), role=role_str)
        refresh_token = auth_service.create_refresh_token(str(citizen.id))

        refresh_hash = auth_service.hash_otp(refresh_token)
        await user_repo.create_session(
            citizen_id=citizen.id,
            refresh_token_hash=refresh_hash,
        )

        logger.info("Citizen registered successfully", extra={"citizen_id": str(citizen.id)})
        user_profile = auth_service.build_profile_response(citizen)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=user_profile,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        logger.error("Database error during citizen registration", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected database error occurred during registration.",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error during citizen registration", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred.",
        ) from exc


@router.post("/request-otp")
async def request_otp(
    phone: str,
    purpose: str = "register",
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Generates, logs in debug mode, and stores OTP for a phone number."""
    masked_phone = _mask_phone(phone)
    logger.debug("OTP request for phone: %s, purpose: %s", masked_phone, purpose)

    try:
        otp_code = auth_service.generate_otp()
        otp_hash = auth_service.hash_otp(otp_code)
        expires_at = datetime.now(UTC) + timedelta(minutes=10)

        await user_repo.create_otp(
            phone=phone,
            code_hash=otp_hash,
            purpose=purpose,
            expires_at=expires_at,
        )

        if settings.debug:
            logger.info("🔑 [DEV OTP CODE] Phone: %s | OTP: %s", phone, otp_code)

        logger.info("OTP generated for phone: %s", masked_phone)
        return {
            "message": f"OTP generated and sent for {phone}",
            "otp": otp_code if settings.debug else None,
        }
    except SQLAlchemyError as exc:
        logger.error("Database error while generating OTP for phone: %s", masked_phone, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected database error occurred while processing OTP request.",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error during OTP generation", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred.",
        ) from exc


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticates a citizen with phone number and password."""
    masked_phone = _mask_phone(payload.phone)
    logger.debug("Login attempt for phone: %s", masked_phone)

    try:
        citizen = await user_repo.get_by_phone(payload.phone)
        if not citizen or not auth_service.verify_password(payload.password, citizen.password_hash):
            logger.warning("Failed login attempt for phone: %s (invalid credentials)", masked_phone)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid mobile number or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not citizen.is_active:
            logger.warning("Failed login attempt for citizen ID %s (account deactivated)", str(citizen.id))
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

        logger.info("Citizen logged in successfully", extra={"citizen_id": str(citizen.id)})
        user_profile = auth_service.build_profile_response(citizen)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=user_profile,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        logger.error("Database error during login", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected database error occurred during login.",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error during login", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred.",
        ) from exc


@router.get("/me", response_model=CitizenProfileResponse)
async def get_me(
    current_user: Citizen = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> CitizenProfileResponse:
    """Returns profile for the currently authenticated user."""
    logger.debug("Retrieving profile for citizen ID: %s", str(current_user.id))
    return auth_service.build_profile_response(current_user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Refreshes access and refresh tokens using a valid refresh token with Refresh Token Rotation."""
    logger.debug("Token refresh request received")

    decoded = auth_service.verify_token(payload.refresh_token, token_type="refresh")
    if not decoded or not decoded.get("sub"):
        logger.warning("Token refresh failed: Invalid or expired refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    try:
        citizen_id = uuid.UUID(decoded["sub"])
    except ValueError as err:
        logger.warning("Token refresh failed: Invalid user ID format in payload sub")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in refresh token",
        ) from err

    try:
        # Verify that this refresh token exists and is active in the database session
        old_refresh_hash = auth_service.hash_otp(payload.refresh_token)
        active_session = await user_repo.get_active_session_by_hash(citizen_id, old_refresh_hash)
        if not active_session:
            logger.warning(
                "Replay attack or invalid refresh token detected for citizen ID %s. Revoking all sessions.",
                str(citizen_id),
            )
            await user_repo.revoke_all_sessions(citizen_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is revoked or invalid. Session terminated.",
            )

        citizen = await user_repo.get_by_id(citizen_id)
        if not citizen or not citizen.is_active:
            logger.warning("Token refresh failed: Citizen ID %s not found or inactive", str(citizen_id))
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

        logger.info("Tokens successfully rotated and refreshed for citizen ID: %s", str(citizen.id))
        user_profile = auth_service.build_profile_response(citizen)
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=user_profile,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        logger.error("Database error during token refresh", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected database error occurred during token refresh.",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error during token refresh", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred.",
        ) from exc


@router.post("/logout")
async def logout(
    payload: RefreshRequest | None = None,
    current_user: Citizen = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """Revokes active refresh token session and logs out user."""
    logger.debug("Logout requested for citizen ID: %s", str(current_user.id))

    try:
        if payload and payload.refresh_token:
            refresh_hash = auth_service.hash_otp(payload.refresh_token)
            await user_repo.revoke_session_by_hash(refresh_hash)
        await user_repo.revoke_all_sessions(current_user.id)

        logger.info("Citizen logged out and sessions revoked", extra={"citizen_id": str(current_user.id)})
        return {"message": "Logged out successfully"}
    except SQLAlchemyError as exc:
        logger.error("Database error during logout for citizen ID: %s", str(current_user.id), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected database error occurred during logout.",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error during logout", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred.",
        ) from exc


@router.post("/verify-otp")
async def verify_otp(
    payload: OTPVerifyRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Verifies OTP code for registration or password reset."""
    masked_phone = _mask_phone(payload.phone)
    logger.debug("OTP verification attempt for phone: %s, purpose: %s", masked_phone, payload.purpose)

    try:
        latest_otp = await user_repo.get_latest_otp(payload.phone, purpose=payload.purpose)

        # Check provided code against hashed code or dev mode wildcard
        provided_hash = auth_service.hash_otp(payload.code)
        valid_code = (
            (latest_otp and latest_otp.code_hash == provided_hash)
            or (settings.debug and payload.code in ("123456", "000000"))
        )

        if not valid_code:
            logger.warning("Invalid OTP code provided for phone: %s", masked_phone)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP code.",
            )

        if settings.debug:
            logger.info("✅ [DEV OTP VERIFIED] Phone: %s | Code: %s", payload.phone, payload.code)

        logger.info("OTP successfully verified for phone: %s", masked_phone)
        return {"verified": True, "message": "OTP verified successfully."}
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        logger.error("Database error during OTP verification", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected database error occurred during OTP verification.",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error during OTP verification", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred.",
        ) from exc
