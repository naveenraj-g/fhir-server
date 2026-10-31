import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=[
            "consent:create",
            "consent:read",
            "consent:update",
            "consent:delete",
            "patient:create",
            "patient:read",
            "practitioner:create",
            "practitioner:read",
            "organization:create",
            "organization:read",
            "observation:create",
            "observation:read",
        ]
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
