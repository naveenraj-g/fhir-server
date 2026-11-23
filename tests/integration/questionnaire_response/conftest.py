import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The response's own scopes, plus the scopes the tests need to create the resources around it (its
# subject, encounter, author, source, basedOn and partOf targets) and the ones to look at what
# points back at it.
RESPONSE_PERMS = [
    "questionnaire_response:create",
    "questionnaire_response:read",
    "questionnaire_response:update",
    "questionnaire_response:delete",
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
    "care_plan:create",
    "care_plan:read",
    "service_request:create",
    "service_request:read",
    "observation:create",
    "observation:read",
    "procedure:create",
    "procedure:read",
    "detected_issue:create",
    "detected_issue:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=RESPONSE_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
