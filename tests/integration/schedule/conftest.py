import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The schedule's own scopes, plus the scopes the tests need to create the
# resources a Schedule's actors can point at.
SCHEDULE_PERMS = [
    "schedule:create",
    "schedule:read",
    "schedule:update",
    "schedule:delete",
    "organization:create",
    "organization:read",
    "practitioner:create",
    "practitioner:read",
    "practitioner_role:create",
    "practitioner_role:read",
    "healthcare_service:create",
    "healthcare_service:read",
    "location:create",
    "location:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=SCHEDULE_PERMS)
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
