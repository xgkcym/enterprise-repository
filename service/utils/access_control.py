from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from service.models.department import DepartmentModel
from service.models.role_department import RoleDepartmentModel
from service.models.users import UserModel
from service.utils.user_types import is_admin_user


async def get_allowed_department_ids(
    *,
    current_user: UserModel,
    session: AsyncSession,
) -> list[int]:
    if is_admin_user(current_user):
        result = await session.execute(
            select(DepartmentModel.dept_id).order_by(DepartmentModel.dept_id)
        )
        return [int(dept_id) for dept_id in result.scalars().all()]

    result = await session.execute(
        select(RoleDepartmentModel.dept_id).where(RoleDepartmentModel.role_id == current_user.role_id)
    )
    department_ids = result.scalars().all()
    deduped_ids: list[int] = []
    seen = set()
    for dept_id in department_ids:
        if dept_id in seen:
            continue
        seen.add(dept_id)
        deduped_ids.append(int(dept_id))
    return deduped_ids


async def get_allowed_departments(
    *,
    current_user: UserModel,
    session: AsyncSession,
) -> list[DepartmentModel]:
    allowed_department_ids = await get_allowed_department_ids(current_user=current_user, session=session)
    if not allowed_department_ids:
        return []

    result = await session.execute(
        select(DepartmentModel)
        .where(DepartmentModel.dept_id.in_(allowed_department_ids))
        .order_by(DepartmentModel.dept_id)
    )
    return result.scalars().all()


async def resolve_authorized_department(
    *,
    current_user: UserModel,
    session: AsyncSession,
    requested_department_id: int | None,
) -> tuple[DepartmentModel, list[int]]:
    allowed_department_ids = await get_allowed_department_ids(current_user=current_user, session=session)
    if not allowed_department_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Current user has no department access",
        )

    target_department_id = requested_department_id
    if target_department_id is None:
        if current_user.dept_id in allowed_department_ids:
            target_department_id = int(current_user.dept_id)
        elif len(allowed_department_ids) == 1:
            target_department_id = allowed_department_ids[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="dept_id is required when multiple departments are allowed",
            )

    if int(target_department_id) not in allowed_department_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to the requested department",
        )

    department_result = await session.execute(
        select(DepartmentModel).where(DepartmentModel.dept_id == int(target_department_id))
    )
    department = department_result.scalar_one_or_none()
    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )

    return department, allowed_department_ids
