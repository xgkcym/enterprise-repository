from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from service.database.connect import get_session
from service.models.users import UserModel
from service.utils.jwt_utils import verify_token

security = HTTPBearer(auto_error=False)


def _credentials_exception(detail: str = "Could not validate credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _ensure_user_is_active(current_user: UserModel) -> None:
    is_active = getattr(current_user, "is_active", True)
    is_disabled = getattr(current_user, "is_disabled", False) or getattr(current_user, "disabled", False)

    if is_active is False or is_disabled is True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> UserModel:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _credentials_exception("Missing bearer token")

    payload = verify_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise _credentials_exception("Invalid token payload")

    result = await session.execute(select(UserModel).where(UserModel.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise _credentials_exception("User not found")

    return user


async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    _ensure_user_is_active(current_user)
    return current_user
