import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=[
            "medication_dispense:create",
            "medication_dispense:read",
            "medication_dispense:update",
            "medication_dispense:delete",
            "patient:create",
            "patient:read",
            "practitioner:create",
            "practitioner:read",
            "location:create",
            "location:read",
        ]
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
