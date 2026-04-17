from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from service.database.connect import get_session
from service.dependencies.auth import get_current_active_user
from service.models.users import UserModel
from service.router.role.index import role_router
from service.utils.access_control import get_allowed_departments


@role_router.get("/department_role", summary="获取当前角色可访问部门")
async def get_department_role(
    current_user: UserModel = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    departments = await get_allowed_departments(current_user=current_user, session=session)
    return {
        "code": 200,
        "message": "ok",
        "data": [
            {
                "dept_id": department.dept_id,
                "dept_name": department.dept_name,
            }
            for department in departments
        ],
    }
