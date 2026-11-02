import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=[
            "risk_assessment:create",
            "risk_assessment:read",
            "risk_assessment:update",
            "risk_assessment:delete",
            "patient:create",
            "patient:read",
            "condition:create",
            "condition:read",
            "practitioner:create",
            "practitioner:read",
            "encounter:create",
            "encounter:read",
            "organization:create",
            "organization:read",
            "observation:create",
            "observation:read",
        ]
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
