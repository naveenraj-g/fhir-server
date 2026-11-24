import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The communication_request's own scopes, plus the scopes the tests need to create the resources around it
# (its subject, encounter, sender, recipients, request, parent) and the ones to look at what
# points back at it.
COMMUNICATION_REQUEST_PERMS = [
    "communication_request:create",
    "communication_request:read",
    "communication_request:update",
    "communication_request:delete",
    "communication:create",
    "communication:read",
    "patient:create",
    "patient:read",
    "group:create",
    "group:read",
    "organization:create",
    "organization:read",
    "practitioner:create",
    "practitioner:read",
    "related_person:create",
    "related_person:read",
    "care_team:create",
    "care_team:read",
    "encounter:create",
    "encounter:read",
    "service_request:create",
    "service_request:read",
    "detected_issue:create",
    "detected_issue:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=COMMUNICATION_REQUEST_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
