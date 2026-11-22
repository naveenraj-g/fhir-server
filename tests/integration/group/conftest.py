import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The group's own scopes, plus the scopes the tests need to create the resources around it (its
# managing entity and members) and the ones to look at what points back at it.
GROUP_PERMS = [
    "group:create",
    "group:read",
    "group:update",
    "group:delete",
    "organization:create",
    "organization:read",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "practitioner_role:create",
    "practitioner_role:read",
    "related_person:create",
    "related_person:read",
    "medication:create",
    "medication:read",
    "detected_issue:create",
    "detected_issue:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=GROUP_PERMS)
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
