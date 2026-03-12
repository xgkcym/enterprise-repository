from fastapi import HTTPException
from fastapi.params import Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from api.database.config import get_session
from api.models.users import UserModel
from api.router.file.index import file_router

@file_router.get()
async def query_file(
        session:AsyncSession = Depends(get_session)
):

    pass


