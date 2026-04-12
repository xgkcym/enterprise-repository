from __future__ import annotations

from sqlmodel import Field, SQLModel

from utils.utils import get_current_time


class UserProfileModel(SQLModel, table=True):
    __tablename__ = "user_profile"

    user_id: int = Field(primary_key=True, foreign_key="users.id")
    answer_style: str = Field(default="standard", index=True)
    preferred_language: str = Field(default="zh-CN", index=True)
    preferred_topics: str = Field(default="")
    prefers_citations: bool = Field(default=True)
    allow_web_search: bool = Field(default=False)
    profile_notes: str = Field(default="")
    created_time: str = Field(default_factory=get_current_time)
    updated_time: str = Field(default_factory=get_current_time)
