import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The medication request's own scopes, plus the scopes the tests need to create the resources
# around it (its subject, encounter, requester, performer, medication, reasons, issues) and the
# ones to look at what points back at it.
MEDICATION_REQUEST_PERMS = [
    "care_team:create",
    "care_team:read",
    "care_plan:create",
    "care_plan:read",
    "medication_request:create",
    "medication_request:read",
    "medication_request:update",
    "medication_request:delete",
    "medication:create",
    "medication:read",
    "service_request:create",
    "service_request:read",
    "observation:create",
    "observation:read",
    "condition:create",
    "condition:read",
    "detected_issue:create",
    "detected_issue:read",
    "diagnostic_report:create",
    "diagnostic_report:read",
    "immunization_recommendation:create",
    "immunization_recommendation:read",
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
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=MEDICATION_REQUEST_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
