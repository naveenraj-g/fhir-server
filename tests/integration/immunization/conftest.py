import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The immunization's own scopes, plus the scopes the tests need to create the
# resources around it (its patient, location, manufacturer, performers, reasons)
# and the ones to look at what points back at it.
IMMUNIZATION_PERMS = [
    "immunization:create",
    "immunization:read",
    "immunization:update",
    "immunization:delete",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "practitioner_role:create",
    "practitioner_role:read",
    "organization:create",
    "organization:read",
    "encounter:create",
    "encounter:read",
    "location:create",
    "location:read",
    "condition:create",
    "condition:read",
    "diagnostic_report:create",
    "diagnostic_report:read",
    "procedure:create",
    "procedure:read",
    "related_person:create",
    "related_person:read",
    "appointment:create",
    "appointment:read",
    "healthcare_service:create",
    "healthcare_service:read",
    "schedule:create",
    "schedule:read",
    "slot:create",
    "slot:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=IMMUNIZATION_PERMS)
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
