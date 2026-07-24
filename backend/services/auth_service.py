import hashlib
import random
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from backend.core.config import settings
from backend.models.citizens import Citizen
from backend.repositories.user import UserRepository
from backend.schemas.auth import CitizenProfileResponse


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def hash_password(self, password: str) -> str:
        pwd_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except Exception:
            return False

    def generate_otp(self) -> str:
        return f"{random.randint(100000, 999999)}"

    def hash_otp(self, otp: str) -> str:
        return hashlib.sha256(otp.encode()).hexdigest()

    def create_access_token(self, citizen_id: str, role: str) -> str:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
        payload = {
            "sub": citizen_id,
            "role": role,
            "exp": expire,
            "type": "access",
            "iat": datetime.now(UTC),
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    def create_refresh_token(self, citizen_id: str) -> str:
        expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
        payload = {
            "sub": citizen_id,
            "exp": expire,
            "type": "refresh",
            "iat": datetime.now(UTC),
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    def verify_token(self, token: str, token_type: str = "access") -> dict[str, Any] | None:
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            if payload.get("type") != token_type:
                return None
            return payload
        except JWTError:
            return None

    def build_profile_response(self, citizen: Citizen) -> CitizenProfileResponse:
        return CitizenProfileResponse(
            id=str(citizen.id),
            display_name=citizen.display_name,
            phone=citizen.phone,
            email=citizen.email,
            preferred_language=(
                str(citizen.preferred_language.value)
                if hasattr(citizen.preferred_language, "value")
                else str(citizen.preferred_language)
            ),
            points=citizen.points,
            is_active=citizen.is_active,
            is_verified=citizen.is_verified,
            role=str(citizen.role.value) if hasattr(citizen.role, "value") else str(citizen.role),
            created_at=citizen.created_at,
        )
