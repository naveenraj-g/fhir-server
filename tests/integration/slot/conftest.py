import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The slot's own scopes, plus the scopes the tests need to create the
# Schedule (and the practitioner it is for) a Slot points at.
SLOT_PERMS = [
    "slot:create",
    "slot:read",
    "slot:update",
    "slot:delete",
    "schedule:create",
    "schedule:read",
    "organization:create",
    "organization:read",
    "practitioner:create",
    "practitioner:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=SLOT_PERMS)
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
