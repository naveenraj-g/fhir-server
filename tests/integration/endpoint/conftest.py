import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The endpoint's own scopes, plus the Organization scopes the tests need to
# create and read the organization an Endpoint is managed by.
ENDPOINT_PERMS = [
    "endpoint:create",
    "endpoint:read",
    "endpoint:update",
    "endpoint:delete",
    "organization:create",
    "organization:read",
    "healthcare_service:create",
    "healthcare_service:read",
    "location:create",
    "location:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=ENDPOINT_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
