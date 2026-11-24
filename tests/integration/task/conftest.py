import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The task's own scopes, plus the scopes the tests need to create the resources around it (its
# subject, focus, encounter, requester, owner, location, parent) and the ones to look at what
# points back at it.
TASK_PERMS = [
    "task:create",
    "task:read",
    "task:update",
    "task:delete",
    "patient:create",
    "patient:read",
    "group:create",
    "group:read",
    "organization:create",
    "organization:read",
    "practitioner:create",
    "practitioner:read",
    "location:create",
    "location:read",
    "encounter:create",
    "encounter:read",
    "service_request:create",
    "service_request:read",
    "care_plan:create",
    "care_plan:read",
    "detected_issue:create",
    "detected_issue:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=TASK_PERMS)
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
