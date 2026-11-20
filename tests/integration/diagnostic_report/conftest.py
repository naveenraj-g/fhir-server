import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The report's own scopes, plus the scopes the tests need to create the resources
# around it (its subject, encounter, performers, and the procedures / encounters
# that point back at it).
REPORT_PERMS = [
    "diagnostic_report:create",
    "diagnostic_report:read",
    "diagnostic_report:update",
    "diagnostic_report:delete",
    "procedure:create",
    "procedure:read",
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
    app.dependency_overrides[get_current_user] = make_test_user(permissions=REPORT_PERMS)
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
