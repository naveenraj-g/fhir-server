import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The care team's own scopes, plus the scopes the tests need to create the resources around it
# (its subject, encounter, participants, reasons, managing organizations) and the ones to look at
# what points back at it.
CARE_TEAM_PERMS = [
    "care_team:create",
    "care_team:read",
    "care_team:update",
    "care_team:delete",
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
    "encounter:create",
    "encounter:read",
    "condition:create",
    "condition:read",
    "group:create",
    "group:read",
    "detected_issue:create",
    "detected_issue:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=CARE_TEAM_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
