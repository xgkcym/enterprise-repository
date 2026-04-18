from fastapi import APIRouter

role_router = APIRouter(prefix="/role", tags=["权限管理"])

from . import admin, department_role
