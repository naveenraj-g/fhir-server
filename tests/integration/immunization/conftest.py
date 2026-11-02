import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=[
            "immunization:create",
            "immunization:read",
            "immunization:update",
            "immunization:delete",
            "patient:create",
            "patient:read",
            "condition:create",
            "condition:read",
            "practitioner:create",
            "practitioner:read",
            "location:create",
            "location:read",
            "organization:create",
            "organization:read",
        ]
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
