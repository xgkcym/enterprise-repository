from __future__ import annotations

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from service.database.connect import get_session
from service.dependencies.auth import get_current_admin_user
from service.models.department import DepartmentModel
from service.models.file import FileModel
from service.models.role import RoleModel
from service.models.role_department import RoleDepartmentModel
from service.models.users import UserModel
from service.router.role.index import role_router


class DepartmentPayload(BaseModel):
    dept_name: str = Field(..., min_length=1, max_length=128)


class RolePayload(BaseModel):
    role_name: str = Field(..., min_length=1, max_length=128)
    dept_ids: list[int] = Field(default_factory=list)


async def _next_department_id(session: AsyncSession) -> int:
    result = await session.execute(select(func.max(DepartmentModel.dept_id)))
    return int(result.scalar() or 0) + 1


async def _next_role_id(session: AsyncSession) -> int:
    result = await session.execute(select(func.max(RoleModel.role_id)))
    return int(result.scalar() or 0) + 1


async def _next_role_department_id(session: AsyncSession) -> int:
    result = await session.execute(select(func.max(RoleDepartmentModel.r_d_id)))
    return int(result.scalar() or 0) + 1


async def _ensure_unique_department_name(
    session: AsyncSession,
    *,
    dept_name: str,
    exclude_dept_id: int | None = None,
) -> None:
    result = await session.execute(
        select(DepartmentModel).where(DepartmentModel.dept_name == dept_name)
    )
    department = result.scalar_one_or_none()
    if department is None:
        return
    if exclude_dept_id is not None and department.dept_id == exclude_dept_id:
        return
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Department name already exists")


async def _ensure_unique_role_name(
    session: AsyncSession,
    *,
    role_name: str,
    exclude_role_id: int | None = None,
) -> None:
    result = await session.execute(select(RoleModel).where(RoleModel.role_name == role_name))
    role = result.scalar_one_or_none()
    if role is None:
        return
    if exclude_role_id is not None and role.role_id == exclude_role_id:
        return
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role name already exists")


async def _validate_department_ids(session: AsyncSession, dept_ids: list[int]) -> list[DepartmentModel]:
    unique_ids = sorted({int(dept_id) for dept_id in dept_ids})
    if not unique_ids:
        return []

    result = await session.execute(
        select(DepartmentModel)
        .where(DepartmentModel.dept_id.in_(unique_ids))
        .order_by(DepartmentModel.dept_id)
    )
    departments = result.scalars().all()
    if len(departments) != len(unique_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more departments were not found")
    return departments


@role_router.get("/admin/meta")
async def get_role_admin_meta(
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    _ = current_user
    result = await session.execute(select(DepartmentModel).order_by(DepartmentModel.dept_id))
    departments = result.scalars().all()
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
            ]
        },
    }


@role_router.get("/admin/departments")
async def list_departments(
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    _ = current_user
    department_result = await session.execute(select(DepartmentModel).order_by(DepartmentModel.dept_id))
    user_count_result = await session.execute(
        select(UserModel.dept_id, func.count(UserModel.id))
        .group_by(UserModel.dept_id)
    )
    file_count_result = await session.execute(
        select(FileModel.dept_id, func.count(FileModel.file_id))
        .where(FileModel.state != "0")
        .group_by(FileModel.dept_id)
    )
    role_count_result = await session.execute(
        select(RoleDepartmentModel.dept_id, func.count(RoleDepartmentModel.role_id))
        .group_by(RoleDepartmentModel.dept_id)
    )

    user_count_map = {int(dept_id): int(count) for dept_id, count in user_count_result.all()}
    file_count_map = {int(dept_id): int(count) for dept_id, count in file_count_result.all()}
    role_count_map = {int(dept_id): int(count) for dept_id, count in role_count_result.all()}

    return {
        "code": 200,
        "message": "success",
        "data": [
            {
                "dept_id": department.dept_id,
                "dept_name": department.dept_name,
                "user_count": user_count_map.get(int(department.dept_id), 0),
                "file_count": file_count_map.get(int(department.dept_id), 0),
                "role_count": role_count_map.get(int(department.dept_id), 0),
            }
            for department in department_result.scalars().all()
        ],
    }


@role_router.post("/admin/departments")
async def create_department(
    payload: DepartmentPayload,
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    _ = current_user
    dept_name = payload.dept_name.strip()
    if not dept_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department name is required")
    await _ensure_unique_department_name(session, dept_name=dept_name)

    department = DepartmentModel(
        dept_id=await _next_department_id(session),
        dept_name=dept_name,
    )
    session.add(department)
    await session.commit()
    await session.refresh(department)
    return {"code": 200, "message": "success", "data": {"dept_id": department.dept_id, "dept_name": department.dept_name}}


@role_router.put("/admin/departments/{dept_id}")
async def update_department(
    dept_id: int,
    payload: DepartmentPayload,
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    _ = current_user
    result = await session.execute(select(DepartmentModel).where(DepartmentModel.dept_id == dept_id))
    department = result.scalar_one_or_none()
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    dept_name = payload.dept_name.strip()
    if not dept_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department name is required")
    await _ensure_unique_department_name(session, dept_name=dept_name, exclude_dept_id=dept_id)

    department.dept_name = dept_name
    session.add(department)
    await session.commit()
    await session.refresh(department)
    return {"code": 200, "message": "success", "data": {"dept_id": department.dept_id, "dept_name": department.dept_name}}


@role_router.delete("/admin/departments/{dept_id}")
async def delete_department(
    dept_id: int,
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    _ = current_user
    result = await session.execute(select(DepartmentModel).where(DepartmentModel.dept_id == dept_id))
    department = result.scalar_one_or_none()
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    user_count = await session.execute(select(func.count(UserModel.id)).where(UserModel.dept_id == dept_id))
    file_count = await session.execute(
        select(func.count(FileModel.file_id)).where(FileModel.dept_id == dept_id, FileModel.state != "0")
    )
    mapping_count = await session.execute(
        select(func.count(RoleDepartmentModel.r_d_id)).where(RoleDepartmentModel.dept_id == dept_id)
    )
    if int(user_count.scalar() or 0) > 0 or int(file_count.scalar() or 0) > 0 or int(mapping_count.scalar() or 0) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department is still referenced by users, files, or role mappings",
        )

    await session.delete(department)
    await session.commit()
    return {"code": 200, "message": "success", "data": {"dept_id": dept_id}}


@role_router.get("/admin/roles")
async def list_roles(
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    _ = current_user
    role_result = await session.execute(select(RoleModel).order_by(RoleModel.role_id))
    mapping_result = await session.execute(
        select(RoleDepartmentModel.role_id, DepartmentModel.dept_id, DepartmentModel.dept_name)
        .join(DepartmentModel, RoleDepartmentModel.dept_id == DepartmentModel.dept_id)
        .order_by(RoleDepartmentModel.role_id, DepartmentModel.dept_id)
    )
    user_count_result = await session.execute(
        select(UserModel.role_id, func.count(UserModel.id))
        .group_by(UserModel.role_id)
    )

    mapping_map: dict[int, list[dict]] = {}
    for role_id, dept_id, dept_name in mapping_result.all():
        mapping_map.setdefault(int(role_id), []).append(
            {"dept_id": int(dept_id), "dept_name": dept_name}
        )
    user_count_map = {int(role_id): int(count) for role_id, count in user_count_result.all()}

    return {
        "code": 200,
        "message": "success",
        "data": [
            {
                "role_id": role.role_id,
                "role_name": role.role_name,
                "departments": mapping_map.get(int(role.role_id), []),
                "dept_ids": [item["dept_id"] for item in mapping_map.get(int(role.role_id), [])],
                "user_count": user_count_map.get(int(role.role_id), 0),
            }
            for role in role_result.scalars().all()
        ],
    }


@role_router.post("/admin/roles")
async def create_role(
    payload: RolePayload,
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    _ = current_user
    role_name = payload.role_name.strip()
    if not role_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role name is required")

    await _ensure_unique_role_name(session, role_name=role_name)
    departments = await _validate_department_ids(session, payload.dept_ids)
    role_id = await _next_role_id(session)
    role = RoleModel(role_id=role_id, role_name=role_name)
    session.add(role)
    next_mapping_id = await _next_role_department_id(session)
    for index, department in enumerate(departments):
        session.add(
            RoleDepartmentModel(
                r_d_id=next_mapping_id + index,
                role_id=role_id,
                dept_id=int(department.dept_id),
            )
        )

    await session.commit()
    return {
        "code": 200,
        "message": "success",
        "data": {
            "role_id": role_id,
            "role_name": role_name,
            "dept_ids": [int(item.dept_id) for item in departments],
        },
    }


@role_router.put("/admin/roles/{role_id}")
async def update_role(
    role_id: int,
    payload: RolePayload,
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    _ = current_user
    result = await session.execute(select(RoleModel).where(RoleModel.role_id == role_id))
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    role_name = payload.role_name.strip()
    if not role_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role name is required")
    await _ensure_unique_role_name(session, role_name=role_name, exclude_role_id=role_id)
    departments = await _validate_department_ids(session, payload.dept_ids)

    role.role_name = role_name
    session.add(role)

    mapping_result = await session.execute(
        select(RoleDepartmentModel).where(RoleDepartmentModel.role_id == role_id)
    )
    for mapping in mapping_result.scalars().all():
        await session.delete(mapping)

    next_mapping_id = await _next_role_department_id(session)
    for index, department in enumerate(departments):
        session.add(
            RoleDepartmentModel(
                r_d_id=next_mapping_id + index,
                role_id=role_id,
                dept_id=int(department.dept_id),
            )
        )

    await session.commit()
    return {
        "code": 200,
        "message": "success",
        "data": {
            "role_id": role_id,
            "role_name": role_name,
            "dept_ids": [int(item.dept_id) for item in departments],
        },
    }


@role_router.delete("/admin/roles/{role_id}")
async def delete_role(
    role_id: int,
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    _ = current_user
    result = await session.execute(select(RoleModel).where(RoleModel.role_id == role_id))
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    user_count = await session.execute(select(func.count(UserModel.id)).where(UserModel.role_id == role_id))
    if int(user_count.scalar() or 0) > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role is still assigned to users")

    mapping_result = await session.execute(
        select(RoleDepartmentModel).where(RoleDepartmentModel.role_id == role_id)
    )
    for mapping in mapping_result.scalars().all():
        await session.delete(mapping)
    await session.delete(role)
    await session.commit()
    return {"code": 200, "message": "success", "data": {"role_id": role_id}}
