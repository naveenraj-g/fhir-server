import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=[
            "task:create",
            "task:read",
            "task:update",
            "task:delete",
            "patient:create",
            "patient:read",
            "organization:create",
            "organization:read",
            "encounter:create",
            "encounter:read",
            "practitioner:create",
            "practitioner:read",
            "location:create",
            "location:read",
        ]
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
