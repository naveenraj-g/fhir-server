import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=[
            "appointment_response:create",
            "appointment_response:read",
            "appointment_response:update",
            "appointment_response:delete",
            "appointment:create",
            "appointment:read",
            "practitioner:create",
            "practitioner:read",
            "location:create",
            "location:read",
            "patient:create",
            "patient:read",
        ]
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
