import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The consent's own scopes, plus the scopes the tests need to create the resources around it (its
# patient, performers, organization, source, actors, data) and the ones to look at what points
# back at it.
CONSENT_PERMS = [
    "consent:create",
    "consent:read",
    "consent:update",
    "consent:delete",
    "patient:create",
    "patient:read",
    "organization:create",
    "organization:read",
    "practitioner:create",
    "practitioner:read",
    "related_person:create",
    "related_person:read",
    "care_team:create",
    "care_team:read",
    "group:create",
    "group:read",
    "document_reference:create",
    "document_reference:read",
    "observation:create",
    "observation:read",
    "detected_issue:create",
    "detected_issue:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=CONSENT_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
