import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The document reference's own scopes, plus the scopes the tests need to create the resources
# around it (its subject, authors, authenticator, custodian, encounter, related resources) and the
# ones to look at what points back at it.
DOCUMENT_PERMS = [
    "document_reference:create",
    "document_reference:read",
    "document_reference:update",
    "document_reference:delete",
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
    "group:create",
    "group:read",
    "encounter:create",
    "encounter:read",
    "episode_of_care:create",
    "episode_of_care:read",
    "condition:create",
    "condition:read",
    "detected_issue:create",
    "detected_issue:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=DOCUMENT_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
