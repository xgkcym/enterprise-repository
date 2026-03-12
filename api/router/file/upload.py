import time
from typing import Tuple

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select,insert,update

from api.database.config import get_session
from api.models.department import DepartmentModel
from api.models.file import FileModel
from api.models.users import UserModel
from api.router.file.index import file_router
from config.settings import settings
from config.types import DocumentMetadata



UPLOAD_DIR = settings.file_dir

@file_router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    dept_id: int = Form(...),
    session: AsyncSession = Depends(get_session)
):

    if not dept_id :
        return {
            "message": "dept_id is required"
        }

    if not user_id:
        return {
            "message": "user_id is required"
        }
    # 验证部门是否存在
    department_result = await session.execute(
        select(DepartmentModel).where(DepartmentModel.dept_id == dept_id)
    )
    department = department_result.first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    department:DepartmentModel = department[0]

    # 验证用户是否存在
    user_result = await session.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = user_result.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")


    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(str(UPLOAD_DIR / department.dept_name), exist_ok=True)
    file_path = str(UPLOAD_DIR / department.dept_name /  file.filename)


    db_filepath = '/' + settings.upload_dir + "/" + department.dept_name + "/" + file.filename
    file_result = await session.execute(
        select(FileModel).where(FileModel.file_path == db_filepath,FileModel.state =='1')
    )
    res_file = file_result.first()
    if res_file:
        new_file_name = ("".join(file.filename.split('.')[:-1]) + '_' + (str(res_file[0].create_time).replace(":",'_')+"."+file.filename.split('.')[-1]))
        new_file_path =  str(UPLOAD_DIR / department.dept_name / new_file_name)

        os.rename(file_path, new_file_path)
        await session.execute(
            update(FileModel)
            .where(FileModel.file_path == db_filepath, FileModel.state == '1')
            .values(
                state='0',
                file_path='/' + settings.upload_dir + "/" + department.dept_name + "/" + new_file_name,
                file_name=new_file_name
            )
        )


    with open(file_path, "wb") as f:
        f.write(await file.read())



    file_data = FileModel(
        user_id=user_id,
        dept_id=department.dept_id,
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        file_name=file.filename,
        file_path=db_filepath,
        file_type=file.filename.split('.')[-1],
    )
    session.add(file_data)
    await session.commit()
    # 保存数据库 metadata
    document = DocumentMetadata(
        file_name=file.filename,
        file_path=db_filepath,
        file_size=file.size,
        file_type=file.filename.split('.')[-1],
        user_id=user_id,
        department=department.dept_name
    )

    return {
        "message": "upload success",
        "document": document,
        "code":200
    }