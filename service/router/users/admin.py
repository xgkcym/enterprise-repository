from __future__ import annotations

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from service.database.connect import get_session
from service.dependencies.auth import get_current_admin_user
from service.models.department import DepartmentModel
from service.models.role import RoleModel
from service.models.users import UserModel
from service.router.users.index import user_router
from service.utils.password_utils import hash_password
from service.utils.user_types import (
    ADMIN_USER_TYPE,
    USER_TYPE_OPTIONS,
    get_user_type_label,
    is_admin_user,
    normalize_user_type,
)


class AdminUserCreateRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    dept_id: int
    role_id: int
    user_type: str = Field(default="user", min_length=1, max_length=20)


class AdminUserUpdateRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    dept_id: int
    role_id: int
    user_type: str = Field(default="user", min_length=1, max_length=20)
    password: str | None = Field(default=None, min_length=6, max_length=128)


def _serialize_user(
    user: UserModel,
    *,
    dept_name: str | None = None,
    role_name: str | None = None,
) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "dept_id": user.dept_id,
        "dept_name": dept_name,
        "role_id": user.role_id,
        "role_name": role_name,
        "user_type": user.user_type,
        "user_type_label": get_user_type_label(user.user_type),
        "is_admin": is_admin_user(user),
        "create_time": user.create_time,
    }


async def _get_department_or_404(session: AsyncSession, dept_id: int) -> DepartmentModel:
    result = await session.execute(select(DepartmentModel).where(DepartmentModel.dept_id == dept_id))
    department = result.scalar_one_or_none()
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return department


async def _get_permission_role_or_404(session: AsyncSession, role_id: int) -> RoleModel:
    result = await session.execute(select(RoleModel).where(RoleModel.role_id == role_id))
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission role not found")
    return role


async def _ensure_unique_username(
    session: AsyncSession,
    *,
    username: str,
    exclude_user_id: int | None = None,
) -> None:
    result = await session.execute(select(UserModel).where(UserModel.username == username))
    existing_user = result.scalar_one_or_none()
    if existing_user is None:
        return
    if exclude_user_id is not None and existing_user.id == exclude_user_id:
        return
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")


@user_router.get("/admin/meta")
async def get_user_management_meta(
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    _ = current_user
    department_result = await session.execute(select(DepartmentModel).order_by(DepartmentModel.dept_id))
    role_result = await session.execute(select(RoleModel).order_by(RoleModel.role_id))
    departments = department_result.scalars().all()
    permission_roles = role_result.scalars().all()
    return {
        "code": 200,
        "message": "success",
        "data": {
            "departments": [
                {
                    "dept_id": department.dept_id,
                    "dept_name": department.dept_name,
                }
                for department in departments
            ],
            "permission_roles": [
                {
                    "role_id": role.role_id,
                    "role_name": role.role_name,
                }
                for role in permission_roles
            ],
            "user_types": list(USER_TYPE_OPTIONS),
        },
    }


@user_router.get("/admin/users")
async def list_users(
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    _ = current_user
    result = await session.execute(
        select(UserModel, DepartmentModel.dept_name, RoleModel.role_name)
        .join(DepartmentModel, UserModel.dept_id == DepartmentModel.dept_id, isouter=True)
        .join(RoleModel, UserModel.role_id == RoleModel.role_id, isouter=True)
        .order_by(UserModel.id.desc())
    )
    return {
        "code": 200,
        "message": "success",
        "data": [
            _serialize_user(user, dept_name=dept_name, role_name=role_name)
            for user, dept_name, role_name in result.all()
        ],
    }


@user_router.post("/admin/users")
async def create_user(
    payload: AdminUserCreateRequest,
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    _ = current_user
    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is required")

    normalized_user_type = normalize_user_type(payload.user_type)
    department = await _get_department_or_404(session, payload.dept_id)
    permission_role = await _get_permission_role_or_404(session, payload.role_id)
    await _ensure_unique_username(session, username=username)

    user = UserModel(
        username=username,
        password=hash_password(payload.password),
        dept_id=payload.dept_id,
        role_id=payload.role_id,
        user_type=normalized_user_type,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return {
        "code": 200,
        "message": "success",
        "data": _serialize_user(
            user,
            dept_name=department.dept_name,
            role_name=permission_role.role_name,
        ),
    }


@user_router.put("/admin/users/{user_id}")
async def update_user(
    user_id: int,
    payload: AdminUserUpdateRequest,
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is required")

    normalized_user_type = normalize_user_type(payload.user_type)
    if user.id == current_user.id and normalized_user_type != ADMIN_USER_TYPE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current admin user cannot remove their own admin access",
        )

    department = await _get_department_or_404(session, payload.dept_id)
    permission_role = await _get_permission_role_or_404(session, payload.role_id)
    await _ensure_unique_username(session, username=username, exclude_user_id=user.id)

    user.username = username
    user.dept_id = payload.dept_id
    user.role_id = payload.role_id
    user.user_type = normalized_user_type
    if payload.password:
        user.password = hash_password(payload.password)

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return {
        "code": 200,
        "message": "success",
        "data": _serialize_user(
            user,
            dept_name=department.dept_name,
            role_name=permission_role.role_name,
        ),
    }
