import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The history's own scopes, plus the scopes the tests need to create the resources around
# it (its patient, reasons and note authors) and the ones to look at what points back at it.
HISTORY_PERMS = [
    "family_member_history:create",
    "family_member_history:read",
    "family_member_history:update",
    "family_member_history:delete",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "practitioner_role:create",
    "practitioner_role:read",
    "organization:create",
    "organization:read",
    "related_person:create",
    "related_person:read",
    "condition:create",
    "condition:read",
    "diagnostic_report:create",
    "diagnostic_report:read",
    "allergy_intolerance:create",
    "allergy_intolerance:read",
    "encounter:create",
    "encounter:read",
    "location:create",
    "location:read",
    "procedure:create",
    "procedure:read",
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
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=HISTORY_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
