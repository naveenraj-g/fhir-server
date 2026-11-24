import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The observation definition's own scopes, plus the ones the tests need to create the resources
# around it (the organization that assigns an identifier, and the activity definition that can
# name it).
OBSERVATION_DEFINITION_PERMS = [
    "observation_definition:create",
    "observation_definition:read",
    "observation_definition:update",
    "observation_definition:delete",
    "organization:create",
    "organization:read",
    "activity_definition:create",
    "activity_definition:read",
    "detected_issue:create",
    "detected_issue:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=OBSERVATION_DEFINITION_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
