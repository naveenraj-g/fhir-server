import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The evaluation's own scopes, plus the scopes the tests need to create the
# resources around it (its patient, authority and the immunization being evaluated)
# and the ones to look at what points back at it.
EVALUATION_PERMS = [
    "immunization_evaluation:create",
    "immunization_evaluation:read",
    "immunization_evaluation:update",
    "immunization_evaluation:delete",
    "immunization_recommendation:create",
    "immunization_recommendation:read",
    "immunization:create",
    "immunization:read",
    "patient:create",
    "patient:read",
    "organization:create",
    "organization:read",
    "practitioner:create",
    "practitioner:read",
    "location:create",
    "location:read",
    "encounter:create",
    "encounter:read",
    "condition:create",
    "condition:read",
    "diagnostic_report:create",
    "diagnostic_report:read",
    "procedure:create",
    "procedure:read",
    "related_person:create",
    "related_person:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=EVALUATION_PERMS)
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
