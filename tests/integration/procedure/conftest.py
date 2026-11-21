import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The procedure's own scopes, plus the scopes the tests need to create the
# resources around it (its subject, encounter, location, performers, reasons,
# and the encounters / appointments that point back at it).
PROCEDURE_PERMS = [
    "procedure:create",
    "procedure:read",
    "procedure:update",
    "procedure:delete",
    "diagnostic_report:create",
    "diagnostic_report:read",
    "condition:create",
    "condition:read",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "practitioner_role:create",
    "practitioner_role:read",
    "related_person:create",
    "related_person:read",
    "organization:create",
    "organization:read",
    "encounter:create",
    "encounter:read",
    "appointment:create",
    "appointment:read",
    "location:create",
    "location:read",
    "healthcare_service:create",
    "healthcare_service:read",
    "schedule:create",
    "schedule:read",
    "slot:create",
    "slot:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=PROCEDURE_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
