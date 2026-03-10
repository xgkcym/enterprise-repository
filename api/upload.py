from fastapi import APIRouter, UploadFile, File, Form
import os

from config.settings import settings
from config.types import DocumentMetadata

router = APIRouter()

UPLOAD_DIR = settings.file_dir

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    department: str = Form(...)
):

    if not department or department.strip() == "":
        return {
            "message": "department is required"
        }

    if not user_id or  user_id.strip() == "":
        return {
            "message": "user_id is required"
        }

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(str(UPLOAD_DIR / department), exist_ok=True)
    file_path = str(UPLOAD_DIR / department /  file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # 保存数据库 metadata
    document = DocumentMetadata(
        file_name=file.filename,
        file_size=file.size,
        file_type=file.content_type,
        user_id=user_id,
        department=department
    )

    return {
        "message": "upload success",
        "document": document
    }