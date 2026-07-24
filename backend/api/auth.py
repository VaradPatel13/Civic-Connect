import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.deps import get_auth_service, get_current_user, get_user_repository
from backend.core.config import settings
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

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Register a new citizen account."""
    existing_phone = await user_repo.get_by_phone(payload.phone)
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number is already registered",
        )

    if payload.email:
        existing_email = await user_repo.get_by_email(payload.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email address is already registered",
            )

    user = await user_repo.create(
        display_name=payload.display_name,
        phone=payload.phone,
        email=payload.email,
        password_hash=service.hash_password(payload.password),
        preferred_language=payload.preferred_language,
        role="citizen",
        is_verified=False,
        is_active=True,
    )

    otp_code = service.generate_otp()
    await user_repo.create_otp(
        citizen_id=user.id,
        phone=payload.phone,
        code_hash=service.hash_password(otp_code),
        purpose="register",
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )

    access_token = service.create_access_token(str(user.id), str(user.role.value if hasattr(user.role, 'value') else user.role))
    refresh_token = service.create_refresh_token(str(user.id))

    await user_repo.create_session(
        citizen_id=user.id,
        refresh_token_hash=service.hash_password(refresh_token),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=service.build_profile_response(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate citizen credentials and return JWT tokens."""
    user = await user_repo.get_by_phone(payload.phone)
    if not user or not service.verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support.",
        )

    role_str = str(user.role.value if hasattr(user.role, "value") else user.role)
    access_token = service.create_access_token(str(user.id), role_str)
    refresh_token = service.create_refresh_token(str(user.id))

    await user_repo.create_session(
        citizen_id=user.id,
        refresh_token_hash=service.hash_password(refresh_token),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=service.build_profile_response(user),
    )


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    payload: OTPVerifyRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Verify citizen registration OTP."""
    user = await user_repo.get_by_phone(payload.phone)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    otp = await user_repo.get_latest_otp(payload.phone, purpose=payload.purpose)
    if not otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP requested for this phone number",
        )

    if otp.is_expired or otp.is_consumed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP code has expired or already been used",
        )

    if otp.attempts >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed OTP attempts. Please request a new code.",
        )

    if not service.verify_password(payload.code, otp.code_hash):
        otp.attempts += 1
        await user_repo.db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP code",
        )

    otp.consumed_at = datetime.now(UTC)
    user.is_verified = True
    await user_repo.db.commit()

    role_str = str(user.role.value if hasattr(user.role, "value") else user.role)
    access_token = service.create_access_token(str(user.id), role_str)
    refresh_token = service.create_refresh_token(str(user.id))

    await user_repo.create_session(
        citizen_id=user.id,
        refresh_token_hash=service.hash_password(refresh_token),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=service.build_profile_response(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Exchange valid refresh token for a new access token and refresh token."""
    decoded = service.verify_token(payload.refresh_token, token_type="refresh")
    if not decoded:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    citizen_id_str = decoded.get("sub")
    try:
        citizen_id = uuid.UUID(citizen_id_str)
    except (ValueError, TypeError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
        ) from err

    user = await user_repo.get_by_id(citizen_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account inactive or missing",
        )

    role_str = str(user.role.value if hasattr(user.role, "value") else user.role)
    new_access_token = service.create_access_token(str(user.id), role_str)
    new_refresh_token = service.create_refresh_token(str(user.id))

    await user_repo.create_session(
        citizen_id=user.id,
        refresh_token_hash=service.hash_password(new_refresh_token),
    )

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=service.build_profile_response(user),
    )


@router.post("/logout")
async def logout(
    current_user: Citizen = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> dict:
    """Revoke all active sessions for the authenticated citizen."""
    await user_repo.revoke_all_sessions(current_user.id)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=CitizenProfileResponse)
async def get_me(
    current_user: Citizen = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> CitizenProfileResponse:
    """Get profile details for the currently authenticated citizen."""
    return service.build_profile_response(current_user)
