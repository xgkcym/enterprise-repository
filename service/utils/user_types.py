from __future__ import annotations

from fastapi import HTTPException, status


ADMIN_USER_TYPE = "admin"
NORMAL_USER_TYPE = "user"

USER_TYPE_OPTIONS = (
    {
        "value": ADMIN_USER_TYPE,
        "label": "管理员",
        "description": "可以进入聊天界面和管理界面",
    },
    {
        "value": NORMAL_USER_TYPE,
        "label": "普通用户",
        "description": "只能进入聊天界面",
    },
)

USER_TYPE_LABELS = {
    ADMIN_USER_TYPE: "管理员",
    NORMAL_USER_TYPE: "普通用户",
}


def normalize_user_type(user_type: str | None) -> str:
    value = (user_type or NORMAL_USER_TYPE).strip().lower()
    if value not in USER_TYPE_LABELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_type",
        )
    return value


def get_user_type_label(user_type: str | None) -> str:
    value = (user_type or NORMAL_USER_TYPE).strip().lower()
    return USER_TYPE_LABELS.get(value, USER_TYPE_LABELS[NORMAL_USER_TYPE])


def is_admin_user(user: object | None) -> bool:
    if user is None:
        return False
    return getattr(user, "user_type", NORMAL_USER_TYPE) == ADMIN_USER_TYPE
