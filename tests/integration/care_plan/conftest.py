import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The care plan's own scopes, plus the scopes the tests need to create the resources around it
# (its subject, encounter, care team, conditions, activity targets and performers) and the ones to
# look at what points back at it.
CARE_PLAN_PERMS = [
    "care_plan:create",
    "care_plan:read",
    "care_plan:update",
    "care_plan:delete",
    "care_team:create",
    "care_team:read",
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
    "healthcare_service:create",
    "healthcare_service:read",
    "location:create",
    "location:read",
    "encounter:create",
    "encounter:read",
    "condition:create",
    "condition:read",
    "goal:create",
    "goal:read",
    "group:create",
    "group:read",
    "appointment:create",
    "appointment:read",
    "medication:create",
    "medication:read",
    "medication_request:create",
    "medication_request:read",
    "service_request:create",
    "service_request:read",
    "detected_issue:create",
    "detected_issue:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=CARE_PLAN_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
