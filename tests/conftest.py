import os
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-google-client")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-google-secret")
os.environ.setdefault("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")


@pytest.fixture
def fake_db() -> MagicMock:
    db = MagicMock(name="db")
    db.commit.return_value = None
    db.refresh.return_value = None
    db.add.return_value = None
    db.delete.return_value = None
    return db


@pytest.fixture
def parent_user() -> Any:
    return SimpleNamespace(
        id=1,
        email="parent@example.com",
        username=None,
        name="Parent User",
        picture=None,
        user_type="parent",
    )


@pytest.fixture
def child_user() -> Any:
    return SimpleNamespace(
        id=2,
        email=None,
        username="child001",
        name="Child User",
        user_type="child",
    )


def build_client(router_module: Any, fake_db: MagicMock, user: Any | None = None) -> TestClient:
    app = FastAPI()
    app.include_router(router_module.router, prefix="/api/v1")

    if hasattr(router_module, "get_db"):
        app.dependency_overrides[router_module.get_db] = lambda: fake_db
    if user is not None and hasattr(router_module, "get_current_user"):
        app.dependency_overrides[router_module.get_current_user] = lambda: user

    return TestClient(app)
