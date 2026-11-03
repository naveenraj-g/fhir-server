import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=[
            "medication_administration:create",
            "medication_administration:read",
            "medication_administration:update",
            "medication_administration:delete",
            "patient:create",
            "patient:read",
            "practitioner:create",
            "practitioner:read",
            "condition:create",
            "condition:read",
        ]
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
