import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The role's own scopes, plus the scopes the tests need to create the
# resources a PractitionerRole points at.
ROLE_PERMS = [
    "practitioner_role:create",
    "practitioner_role:read",
    "practitioner_role:update",
    "practitioner_role:delete",
    "practitioner:create",
    "practitioner:read",
    "organization:create",
    "organization:read",
    "location:create",
    "location:read",
    "healthcare_service:create",
    "healthcare_service:read",
    "endpoint:create",
    "endpoint:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=ROLE_PERMS)
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
