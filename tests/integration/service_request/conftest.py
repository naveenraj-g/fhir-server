import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The service request's own scopes, plus the scopes the tests need to create the resources
# around it (its subject, encounter, requester, performers, specimens, reasons) and the ones to
# look at what points back at it.
SERVICE_REQUEST_PERMS = [
    "medication_request:create",
    "medication_request:read",
    "service_request:create",
    "service_request:read",
    "service_request:update",
    "service_request:delete",
    "specimen:create",
    "specimen:read",
    "observation:create",
    "observation:read",
    "diagnostic_report:create",
    "diagnostic_report:read",
    "procedure:create",
    "procedure:read",
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
        permissions=SERVICE_REQUEST_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
