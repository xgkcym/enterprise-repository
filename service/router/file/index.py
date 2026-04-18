from fastapi import APIRouter

file_router = APIRouter(prefix="/file", tags=["文件模块"])
legacy_public_file_router = APIRouter(tags=["文件模块"])

from . import admin, download, query, upload
