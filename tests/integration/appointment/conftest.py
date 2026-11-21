import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The appointment's own scopes, plus the scopes the tests need to create the
# resources an Appointment points at (patient, practitioner, location, ...).
APPOINTMENT_PERMS = [
    "condition:create",
    "condition:read",
    "related_person:create",
    "related_person:read",
    "appointment:create",
    "appointment:read",
    "appointment:update",
    "appointment:delete",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "practitioner_role:create",
    "practitioner_role:read",
    "healthcare_service:create",
    "healthcare_service:read",
    "location:create",
    "location:read",
    "organization:create",
    "organization:read",
    "schedule:create",
    "schedule:read",
    "slot:create",
    "slot:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=APPOINTMENT_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
