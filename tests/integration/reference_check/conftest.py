import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.integration.reference_check.cases import CASES, permission_name

# create / read / update on every resource the test writes to
PERMS = [
    f"{permission_name(resource_type)}:{action}"
    for resource_type in CASES
    for action in ("create", "read", "update")
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=PERMS)
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
