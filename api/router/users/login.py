

from datetime import datetime, timedelta
from fastapi import Form, Depends, HTTPException
from openai import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.database.config import get_session
from api.models.users import UserModel
from api.router.users.index import user_router
from api.utils.jwt_utils import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from api.dependencies.auth import get_current_user, get_current_active_user
import hashlib


# MD5 加密密码（建议使用更安全的 bcrypt，但这里保持与你原代码一致）
def md5_hex(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()

class LoginRequest(BaseModel):  # 新增模型
    username: str
    password: str

@user_router.post("/login", summary="用户登录")
async def login(
        body: LoginRequest,
        session: AsyncSession = Depends(get_session)
):
    """
    用户登录接口
    成功返回 JWT Token，失败返回 401
    """
    # MD5 加密密码
    hashed_password = md5_hex(body.password)
    print(hashed_password)
    # 查询用户
    result = await session.execute(
        select(UserModel).where(UserModel.username == body.username,UserModel.password == hashed_password)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )

    # 创建 Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )

    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "username": user.username,
                "dept_id": user.dept_id,
                "role_id": user.role_id
            }
        }
    }



