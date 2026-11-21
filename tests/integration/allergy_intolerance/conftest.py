import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The allergy's own scopes, plus the scopes the tests need to create the
# resources around it (its patient, encounter, recorder / asserter ...).
ALLERGY_PERMS = [
    "allergy_intolerance:create",
    "allergy_intolerance:read",
    "allergy_intolerance:update",
    "allergy_intolerance:delete",
    "patient:create",
    "patient:read",
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
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=ALLERGY_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
