from __future__ import annotations

from fastapi import Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from service.database.connect import get_session
from service.dependencies.auth import get_current_active_user
from service.models.users import UserModel
from service.router.users.index import user_router
from service.utils.user_profile import (
    get_or_create_user_profile,
    profile_model_to_dict,
    update_user_profile,
)


class UserProfileUpdateRequest(BaseModel):
    answer_style: str = Field(default="standard", pattern="^(concise|standard|detailed)$")
    preferred_language: str = Field(default="zh-CN", max_length=20)
    preferred_topics: list[str] = Field(default_factory=list)
    prefers_citations: bool = Field(default=True)
    allow_web_search: bool = Field(default=False)
    profile_notes: str = Field(default="", max_length=1000)


@user_router.get("/profile")
async def get_my_profile(
    current_user: UserModel = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    profile = await get_or_create_user_profile(session=session, current_user=current_user)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "user_id": current_user.id,
            **profile_model_to_dict(profile),
        },
    }


@user_router.put("/profile")
async def update_my_profile(
    payload: UserProfileUpdateRequest,
    current_user: UserModel = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    profile = await update_user_profile(
        session=session,
        current_user=current_user,
        answer_style=payload.answer_style,
        preferred_language=payload.preferred_language,
        preferred_topics=payload.preferred_topics,
        prefers_citations=payload.prefers_citations,
        allow_web_search=payload.allow_web_search,
        profile_notes=payload.profile_notes,
    )
    return {
        "code": 200,
        "message": "success",
        "data": {
            "user_id": current_user.id,
            **profile_model_to_dict(profile),
        },
    }
