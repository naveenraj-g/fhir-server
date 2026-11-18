import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The service's own scopes, plus the Organization/Location scopes the tests need to
# create and read the resources a HealthcareService points at.
HS_PERMS = [
    "healthcare_service:create",
    "healthcare_service:read",
    "healthcare_service:update",
    "healthcare_service:delete",
    "organization:create",
    "organization:read",
    "location:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=HS_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
