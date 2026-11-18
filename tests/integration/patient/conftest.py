import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The patient's own scopes (including the link permission), plus the scopes the
# tests need to create the organization / practitioner a Patient references.
PATIENT_PERMS = [
    "patient:create",
    "patient:read",
    "patient:update",
    "patient:delete",
    "patient:link",
    "organization:create",
    "organization:read",
    "practitioner:create",
    "practitioner:read",
    "practitioner_role:create",
    "practitioner_role:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=PATIENT_PERMS)
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
