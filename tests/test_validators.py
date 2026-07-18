from __future__ import annotations

import pytest

from backend.core.validators import (
    ValidationError,
    validate_account_name,
    validate_username,
)


@pytest.mark.parametrize(
    "name",
    ["木木44", "账号一", "mumu44", "木木_mumu-44"],
)
def test_account_name_accepts_chinese_and_ascii(name: str) -> None:
    assert validate_account_name(name) == name


@pytest.mark.parametrize("name", ["木 木", "木木/44", "木木@44", ""])
def test_account_name_rejects_unsafe_characters(name: str) -> None:
    with pytest.raises(ValidationError):
        validate_account_name(name)


def test_admin_username_remains_ascii_only() -> None:
    with pytest.raises(ValidationError):
        validate_username("管理员")
