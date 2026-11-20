import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The related person's own scopes, plus the scopes the tests need to create the
# resources around it (its patient, an appointment / encounter that names it ...).
RELATED_PERSON_PERMS = [
    "related_person:create",
    "related_person:read",
    "related_person:update",
    "related_person:delete",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "organization:create",
    "organization:read",
    "appointment:create",
    "appointment:read",
    "appointment_response:create",
    "appointment_response:read",
    "encounter:create",
    "encounter:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=RELATED_PERSON_PERMS)
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
