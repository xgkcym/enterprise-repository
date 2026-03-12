from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from api.database.config import get_session
from api.dependencies.auth import get_current_active_user
from api.models.role_department import RoleDepartmentModel
from api.models.users import UserModel
from api.router.role.index import role_router


@role_router.get("/department_role", summary="获取部门角色")
async def get_department_role(current_user:UserModel=Depends(get_current_active_user),session:AsyncSession=Depends(get_session)):
    res = await session.execute(
        select(RoleDepartmentModel).where(
            RoleDepartmentModel.dept_id == current_user.dept_id
        )
    )
    return {
        "code": 200,
        "message": "ok",
        "data": {
            "department_role": str(res)
        }
    }