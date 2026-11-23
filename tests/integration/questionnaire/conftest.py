import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The questionnaire's own scopes, plus the ones the tests need to create the resources around it
# (the organization that assigns an identifier, a QuestionnaireResponse that names it).
QUESTIONNAIRE_PERMS = [
    "questionnaire:create",
    "questionnaire:read",
    "questionnaire:update",
    "questionnaire:delete",
    "questionnaire_response:create",
    "questionnaire_response:read",
    "organization:create",
    "organization:read",
    "patient:create",
    "patient:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=QUESTIONNAIRE_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
