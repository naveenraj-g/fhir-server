import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The resource's own scopes, plus the scopes the tests need to create the resources it can
# point at (its manufacturer, associated medication, monograph document, contraindication).
MEDICATION_KNOWLEDGE_PERMS = [
    "medication_knowledge:create",
    "medication_knowledge:read",
    "medication_knowledge:update",
    "medication_knowledge:delete",
    "organization:create",
    "organization:read",
    "medication:create",
    "medication:read",
    "document_reference:create",
    "document_reference:read",
    "detected_issue:create",
    "detected_issue:read",
    "patient:create",
    "patient:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=MEDICATION_KNOWLEDGE_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
