from datetime import timedelta

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.settings import settings
from service.database.connect import get_session
from service.models.users import UserModel
from service.router.users.index import user_router
from service.utils.jwt_utils import create_access_token
from service.utils.password_utils import verify_and_upgrade_password
from service.utils.user_types import is_admin_user


class LoginRequest(BaseModel):
    username: str
    password: str


@user_router.post("/login", summary="用户登录")
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    username = body.username.strip()
    result = await session.execute(
        select(UserModel).where(UserModel.username == username)
    )
    user = result.scalar_one_or_none()

    verified = False
    upgraded_password_hash: str | None = None
    if user is not None:
        verified, upgraded_password_hash = verify_and_upgrade_password(body.password, user.password)

    if not user or not verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if upgraded_password_hash and upgraded_password_hash != user.password:
        user.password = upgraded_password_hash
        session.add(user)
        await session.commit()
        await session.refresh(user)

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "dept_id": user.dept_id,
            "role_id": user.role_id,
            "user_type": user.user_type,
        },
        expires_delta=access_token_expires,
    )

    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "user": {
                "id": user.id,
                "username": user.username,
                "dept_id": user.dept_id,
                "role_id": user.role_id,
                "user_type": user.user_type,
                "is_admin": is_admin_user(user),
            },
        },
    }
