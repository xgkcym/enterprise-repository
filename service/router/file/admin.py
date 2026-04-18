from __future__ import annotations

from pathlib import Path

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from service.database.connect import get_session
from service.dependencies.auth import get_current_admin_user
from service.models.department import DepartmentModel
from service.models.file import FileModel
from service.models.users import UserModel
from service.router.file.index import file_router
from service.utils.file_utils import build_file_download_url, resolve_storage_path


FILE_STATE_LABELS = {
    "0": "Deleted",
    "1": "Ready",
    "2": "Processing",
    "3": "Pending",
    "4": "Failed",
}


def _serialize_file(file_item: FileModel, *, dept_name: str | None = None, username: str | None = None) -> dict:
    return {
        "file_id": file_item.file_id,
        "user_id": file_item.user_id,
        "username": username,
        "dept_id": file_item.dept_id,
        "dept_name": dept_name,
        "create_time": file_item.create_time,
        "file_name": file_item.file_name,
        "file_type": file_item.file_type,
        "state": file_item.state,
        "state_label": FILE_STATE_LABELS.get(file_item.state, file_item.state),
        "file_path": file_item.file_path,
        "download_url": build_file_download_url(int(file_item.file_id)),
    }


@file_router.get("/admin/files")
async def list_admin_files(
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    _ = current_user
    result = await session.execute(
        select(FileModel, DepartmentModel.dept_name, UserModel.username)
        .join(DepartmentModel, FileModel.dept_id == DepartmentModel.dept_id, isouter=True)
        .join(UserModel, FileModel.user_id == UserModel.id, isouter=True)
        .order_by(FileModel.create_time.desc())
    )
    return {
        "code": 200,
        "message": "success",
        "data": [
            _serialize_file(file_item, dept_name=dept_name, username=username)
            for file_item, dept_name, username in result.all()
        ],
    }


@file_router.delete("/admin/files/{file_id}")
async def delete_admin_file(
    file_id: int,
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    _ = current_user
    result = await session.execute(
        select(FileModel, DepartmentModel)
        .join(DepartmentModel, FileModel.dept_id == DepartmentModel.dept_id, isouter=True)
        .where(FileModel.file_id == file_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    file_item, department = row
    if department is not None:
        storage_path = resolve_storage_path(
            department_name=department.dept_name,
            file_name=file_item.file_name,
        )
        if Path(storage_path).exists():
            Path(storage_path).unlink()

    file_item.state = "0"
    session.add(file_item)
    await session.commit()
    return {"code": 200, "message": "success", "data": {"file_id": file_id}}
