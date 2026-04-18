from __future__ import annotations

import logging

from sqlalchemy import func
from sqlmodel import select

from core.settings import settings
from service.database.connect import async_session_maker
from service.models.department import DepartmentModel
from service.models.role import RoleModel
from service.models.role_department import RoleDepartmentModel
from service.models.users import UserModel
from service.utils.password_utils import hash_password
from service.utils.user_types import ADMIN_USER_TYPE


logger = logging.getLogger(__name__)


async def ensure_bootstrap_admin() -> None:
    if not settings.bootstrap_admin_enabled:
        logger.info("Bootstrap admin is disabled.")
        return

    async with async_session_maker() as session:
        existing_admin_result = await session.execute(
            select(UserModel).where(UserModel.user_type == ADMIN_USER_TYPE).limit(1)
        )
        existing_admin = existing_admin_result.scalar_one_or_none()
        if existing_admin is not None:
            logger.info("Bootstrap admin skipped because an admin user already exists: %s", existing_admin.username)
            return

        department_result = await session.execute(
            select(DepartmentModel).where(DepartmentModel.dept_id == settings.bootstrap_admin_dept_id)
        )
        department = department_result.scalar_one_or_none()
        if department is None:
            department = DepartmentModel(
                dept_id=settings.bootstrap_admin_dept_id,
                dept_name=settings.bootstrap_admin_dept_name,
            )
            session.add(department)

        role_result = await session.execute(
            select(RoleModel).where(RoleModel.role_id == settings.bootstrap_admin_role_id)
        )
        role = role_result.scalar_one_or_none()
        if role is None:
            role = RoleModel(
                role_id=settings.bootstrap_admin_role_id,
                role_name=settings.bootstrap_admin_role_name,
            )
            session.add(role)

        await session.flush()

        role_department_result = await session.execute(
            select(RoleDepartmentModel).where(
                RoleDepartmentModel.role_id == settings.bootstrap_admin_role_id,
                RoleDepartmentModel.dept_id == settings.bootstrap_admin_dept_id,
            )
        )
        role_department = role_department_result.scalar_one_or_none()
        if role_department is None:
            max_id_result = await session.execute(select(func.max(RoleDepartmentModel.r_d_id)))
            next_role_department_id = int(max_id_result.scalar() or 0) + 1
            session.add(
                RoleDepartmentModel(
                    r_d_id=next_role_department_id,
                    role_id=settings.bootstrap_admin_role_id,
                    dept_id=settings.bootstrap_admin_dept_id,
                )
            )

        user_result = await session.execute(
            select(UserModel).where(UserModel.username == settings.bootstrap_admin_username)
        )
        user = user_result.scalar_one_or_none()
        password_hash = hash_password(settings.bootstrap_admin_password)

        if user is None:
            user = UserModel(
                username=settings.bootstrap_admin_username,
                password=password_hash,
                dept_id=settings.bootstrap_admin_dept_id,
                role_id=settings.bootstrap_admin_role_id,
                user_type=ADMIN_USER_TYPE,
            )
            session.add(user)
            action = "created"
        else:
            user.password = password_hash
            user.dept_id = settings.bootstrap_admin_dept_id
            user.role_id = settings.bootstrap_admin_role_id
            user.user_type = ADMIN_USER_TYPE
            session.add(user)
            action = "updated"

        await session.commit()
        logger.warning(
            "Bootstrap admin %s. username=%s, dept_id=%s, role_id=%s",
            action,
            settings.bootstrap_admin_username,
            settings.bootstrap_admin_dept_id,
            settings.bootstrap_admin_role_id,
        )
