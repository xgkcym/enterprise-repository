from fastapi import Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from service.database.connect import get_session
from service.dependencies.auth import get_current_active_user
from service.models.department import DepartmentModel
from service.models.file import FileModel
from service.models.users import UserModel
from service.router.file.index import file_router, legacy_public_file_router
from service.utils.access_control import get_allowed_department_ids
from service.utils.file_utils import guess_media_type, resolve_storage_path


async def _get_authorized_file_record(
    *,
    session: AsyncSession,
    current_user: UserModel,
    file_id: int | None = None,
    department_name: str | None = None,
    file_name: str | None = None,
) -> tuple[FileModel, DepartmentModel]:
    allowed_department_ids = await get_allowed_department_ids(current_user=current_user, session=session)
    if not allowed_department_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No department access")

    query = (
        select(FileModel, DepartmentModel)
        .join(DepartmentModel, FileModel.dept_id == DepartmentModel.dept_id)
        .where(
            FileModel.dept_id.in_(allowed_department_ids),
            FileModel.state != "0",
            FileModel.state != "4",
        )
    )
    if file_id is not None:
        query = query.where(FileModel.file_id == file_id)
    if department_name is not None:
        query = query.where(DepartmentModel.dept_name == department_name)
    if file_name is not None:
        query = query.where(FileModel.file_name == file_name)

    result = await session.execute(query)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    file_item, department = row
    storage_path = resolve_storage_path(
        department_name=department.dept_name,
        file_name=file_item.file_name,
    )
    if not storage_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found")

    return file_item, department


@file_router.get("/files/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    file_item, department = await _get_authorized_file_record(
        session=session,
        current_user=current_user,
        file_id=file_id,
    )
    storage_path = resolve_storage_path(
        department_name=department.dept_name,
        file_name=file_item.file_name,
    )
    return FileResponse(
        path=str(storage_path),
        media_type=guess_media_type(file_item.file_name),
        filename=file_item.file_name,
    )


@legacy_public_file_router.get("/public/uploads/{department_name}/{file_name:path}", include_in_schema=False)
async def download_legacy_public_file(
    department_name: str,
    file_name: str,
    current_user: UserModel = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    file_item, department = await _get_authorized_file_record(
        session=session,
        current_user=current_user,
        department_name=department_name,
        file_name=file_name,
    )
    storage_path = resolve_storage_path(
        department_name=department.dept_name,
        file_name=file_item.file_name,
    )
    return FileResponse(
        path=str(storage_path),
        media_type=guess_media_type(file_item.file_name),
        filename=file_item.file_name,
    )
