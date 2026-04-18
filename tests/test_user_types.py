from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from service.utils.user_types import (
    ADMIN_USER_TYPE,
    NORMAL_USER_TYPE,
    get_user_type_label,
    is_admin_user,
    normalize_user_type,
)


def test_normalize_user_type_accepts_admin_and_user() -> None:
    assert normalize_user_type("admin") == ADMIN_USER_TYPE
    assert normalize_user_type("USER") == NORMAL_USER_TYPE


def test_normalize_user_type_rejects_invalid_value() -> None:
    with pytest.raises(HTTPException):
        normalize_user_type("manager")


def test_is_admin_user_uses_user_type_field() -> None:
    assert is_admin_user(SimpleNamespace(user_type="admin")) is True
    assert is_admin_user(SimpleNamespace(user_type="user")) is False


def test_get_user_type_label_has_expected_labels() -> None:
    assert get_user_type_label("admin") == "管理员"
    assert get_user_type_label("user") == "普通用户"
