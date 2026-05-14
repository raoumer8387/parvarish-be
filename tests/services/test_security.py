import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from app.core import security
from app.core.config import settings


@pytest.mark.unit
def test_create_access_token_and_decode_roundtrip():
    token = security.create_access_token({"sub": "42", "email": "a@b.com"})
    payload = security.jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "42"
    assert payload["email"] == "a@b.com"
    assert "exp" in payload


@pytest.mark.unit
def test_password_hash_and_verify_roundtrip():
    h = security.get_password_hash("secretpass")
    assert security.verify_password("secretpass", h) is True
    assert security.verify_password("wrong", h) is False


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_current_user_returns_user_from_db():
    db = MagicMock()
    user_obj = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user_obj
    token = security.create_access_token({"sub": "7"})

    out = await security.get_current_user(token=token, db=db)
    assert out is user_obj


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_current_user_missing_token_raises():
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        await security.get_current_user(token=None, db=db)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_current_user_optional_no_token():
    db = MagicMock()
    out = await security.get_current_user_optional(token=None, db=db)
    assert out is None
