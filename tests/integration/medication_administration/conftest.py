import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The administration's own scopes, plus the scopes the tests need to create the resources around it
# (its subject, context, performer, medication, request and reason targets) and the ones to look at
# what points back at it.
ADMIN_PERMS = [
    "medication_administration:create",
    "medication_administration:read",
    "medication_administration:update",
    "medication_administration:delete",
    "medication_request:create",
    "medication_request:read",
    "patient:create",
    "patient:read",
    "group:create",
    "group:read",
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
    "episode_of_care:create",
    "episode_of_care:read",
    "medication:create",
    "medication:read",
    "observation:create",
    "observation:read",
    "procedure:create",
    "procedure:read",
    "condition:create",
    "condition:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=ADMIN_PERMS)
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
