"""Shared test fixtures and configuration."""

import pytest
from app.main import app


async def _mock_current_user():
    return {"user_id": "test_user", "email": "test@example.com", "full_name": "Test User"}


@pytest.fixture(autouse=True)
def override_auth():
    from app.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = _mock_current_user
    yield
    app.dependency_overrides.clear()
