import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.citizens import Citizen
from backend.repositories.user import UserRepository
from backend.services.auth_service import AuthService

security = HTTPBearer(auto_error=False)


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
) -> Citizen:
    if not credentials:
        demo_user = await user_repo.get_by_email("demo@civicconnect.gov.in")
        if not demo_user:
            demo_user = await user_repo.get_by_phone("+919999999999")
        if not demo_user:
            demo_user = await user_repo.create(
                phone="+919999999999",
                email="demo@civicconnect.gov.in",
                display_name="Demo Citizen",
                password_hash="demo_hash_placeholder",
                is_active=True,
            )
        return demo_user

    token = credentials.credentials
    payload = auth_service.verify_token(token, token_type="access")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    citizen_id_str = payload.get("sub")
    if not citizen_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        citizen_id = uuid.UUID(citizen_id_str)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token sub format",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    citizen = await user_repo.get_by_id(citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found",
        )

    if not citizen.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return citizen
