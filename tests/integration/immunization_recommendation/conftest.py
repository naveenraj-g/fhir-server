import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=[
            "immunization_recommendation:create",
            "immunization_recommendation:read",
            "immunization_recommendation:update",
            "immunization_recommendation:delete",
            "patient:create",
            "patient:read",
            "organization:create",
            "organization:read",
            "immunization:create",
            "immunization:read",
            "condition:create",
            "condition:read",
            "observation:create",
            "observation:read",
        ]
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
