import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

# The report's own scopes, plus the scopes the tests need to create the resources around it (its
# subject, reporter, evaluated resources and measure) and the ones to look at what points back at
# it.
MEASURE_REPORT_PERMS = [
    "measure_report:create",
    "measure_report:read",
    "measure_report:update",
    "measure_report:delete",
    "measure:create",
    "measure:read",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "organization:create",
    "organization:read",
    "group:create",
    "group:read",
    "location:create",
    "location:read",
    "observation:create",
    "observation:read",
    "detected_issue:create",
    "detected_issue:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=MEASURE_REPORT_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
