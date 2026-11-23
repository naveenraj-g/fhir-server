import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The episode's own scopes, plus the scopes the tests need to create the resources around it
# (its patient, managing organization, care manager, diagnoses, referrals, team) and the ones to
# look at what points back at it (encounters).
EPISODE_PERMS = [
    "episode_of_care:create",
    "episode_of_care:read",
    "episode_of_care:update",
    "episode_of_care:delete",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "practitioner_role:create",
    "practitioner_role:read",
    "organization:create",
    "organization:read",
    "condition:create",
    "condition:read",
    "service_request:create",
    "service_request:read",
    "care_team:create",
    "care_team:read",
    "encounter:create",
    "encounter:read",
    "detected_issue:create",
    "detected_issue:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=EPISODE_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
