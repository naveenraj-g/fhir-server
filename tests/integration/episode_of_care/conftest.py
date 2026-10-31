import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=[
            "episode_of_care:create",
            "episode_of_care:read",
            "episode_of_care:update",
            "episode_of_care:delete",
            "patient:create",
            "patient:read",
            "practitioner:create",
            "practitioner:read",
            "organization:create",
            "organization:read",
            "condition:create",
            "condition:read",
            "care_team:create",
            "care_team:read",
        ]
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
