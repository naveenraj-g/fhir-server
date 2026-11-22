import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The service request's own scopes, plus the scopes the tests need to create the resources
# around it (its subject, encounter, requester, performers, specimens, reasons) and the ones to
# look at what points back at it.
MEDICATION_PERMS = [
    "medication:create",
    "medication:read",
    "medication:update",
    "medication:delete",
    "organization:create",
    "organization:read",
    "detected_issue:create",
    "detected_issue:read",
    "clinical_impression:create",
    "clinical_impression:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=MEDICATION_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
