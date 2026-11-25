import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The measure's own scopes, plus the ones the tests need to create the resources
# around it (the organization that assigns an identifier, a patient, a location/medication it
# names, the detected issue and communication request that can name it).
MEASURE_PERMS = [
    "measure:create",
    "measure:read",
    "measure:update",
    "measure:delete",
    "organization:create",
    "organization:read",
    "patient:create",
    "patient:read",
    "group:create",
    "group:read",
    "location:create",
    "location:read",
    "medication:create",
    "medication:read",
    "detected_issue:create",
    "detected_issue:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=MEASURE_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
