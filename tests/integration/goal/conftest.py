import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The goal's own scopes, plus the scopes the tests need to create the resources around it (its
# subject, expressedBy, addresses, outcomes) and the ones to look at what points back at it.
GOAL_PERMS = [
    "goal:create",
    "goal:read",
    "goal:update",
    "goal:delete",
    "patient:create",
    "patient:read",
    "group:create",
    "group:read",
    "organization:create",
    "organization:read",
    "practitioner:create",
    "practitioner:read",
    "condition:create",
    "condition:read",
    "observation:create",
    "observation:read",
    "encounter:create",
    "encounter:read",
    "care_plan:create",
    "care_plan:read",
    "medication_statement:create",
    "medication_statement:read",
    "detected_issue:create",
    "detected_issue:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=GOAL_PERMS)
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
