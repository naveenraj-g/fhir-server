import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=[
            "clinical_impression:create",
            "clinical_impression:read",
            "clinical_impression:update",
            "clinical_impression:delete",
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
            "risk_assessment:create",
            "risk_assessment:read",
        ]
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
