from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from service.models.user_profile import UserProfileModel
from service.models.users import UserModel
from utils.utils import get_current_time


DEFAULT_PROFILE = {
    "answer_style": "standard",
    "preferred_language": "zh-CN",
    "preferred_topics": [],
    "prefers_citations": True,
    "allow_web_search": False,
    "profile_notes": "",
}


def _normalize_topics(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = [item.strip() for item in text.split(",")]
    elif isinstance(value, (list, tuple, set)):
        parsed = list(value)
    else:
        parsed = [str(value)]

    topics: list[str] = []
    seen = set()
    for item in parsed:
        topic = str(item).strip()
        if not topic or topic in seen:
            continue
        seen.add(topic)
        topics.append(topic)
    return topics[:10]


def _serialize_topics(topics: Any) -> str:
    return json.dumps(_normalize_topics(topics), ensure_ascii=False)


def profile_model_to_dict(profile: UserProfileModel | None) -> dict[str, Any]:
    if not profile:
        return dict(DEFAULT_PROFILE)
    return {
        "answer_style": profile.answer_style or DEFAULT_PROFILE["answer_style"],
        "preferred_language": profile.preferred_language or DEFAULT_PROFILE["preferred_language"],
        "preferred_topics": _normalize_topics(profile.preferred_topics),
        "prefers_citations": bool(profile.prefers_citations),
        "allow_web_search": bool(profile.allow_web_search),
        "profile_notes": profile.profile_notes or "",
    }


async def get_or_create_user_profile(
    *,
    session: AsyncSession,
    current_user: UserModel,
) -> UserProfileModel:
    result = await session.execute(
        select(UserProfileModel).where(UserProfileModel.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if profile:
        return profile

    profile = UserProfileModel(user_id=int(current_user.id))
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


async def update_user_profile(
    *,
    session: AsyncSession,
    current_user: UserModel,
    answer_style: str | None = None,
    preferred_language: str | None = None,
    preferred_topics: Any = None,
    prefers_citations: bool | None = None,
    allow_web_search: bool | None = None,
    profile_notes: str | None = None,
) -> UserProfileModel:
    profile = await get_or_create_user_profile(session=session, current_user=current_user)
    if answer_style is not None:
        profile.answer_style = answer_style
    if preferred_language is not None:
        profile.preferred_language = preferred_language
    if preferred_topics is not None:
        profile.preferred_topics = _serialize_topics(preferred_topics)
    if prefers_citations is not None:
        profile.prefers_citations = prefers_citations
    if allow_web_search is not None:
        profile.allow_web_search = allow_web_search
    if profile_notes is not None:
        profile.profile_notes = profile_notes.strip()
    profile.updated_time = get_current_time()
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


def build_user_profile_payload(
    *,
    current_user: UserModel,
    allowed_department_ids: list[int],
    profile: UserProfileModel | None,
) -> dict[str, Any]:
    profile_dict = profile_model_to_dict(profile)
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "dept_id": current_user.dept_id,
        "department_id": current_user.dept_id,
        "role_id": current_user.role_id,
        "allowed_department_ids": allowed_department_ids,
        **profile_dict,
    }
