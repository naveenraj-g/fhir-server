import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.groups import seed_groups
from tests.helpers.observations import seed_observations

# The condition's own scopes, plus the scopes the tests need to create the
# resources around it (its subject, encounter, recorder / asserter, and the
# encounters / appointments that point back at it).
CONDITION_PERMS = [
    "group:create",
    "group:read",
    "observation:create",
    "observation:read",
    "diagnostic_report:create",
    "diagnostic_report:read",
    "clinical_impression:create",
    "clinical_impression:read",
    "condition:create",
    "condition:read",
    "condition:update",
    "condition:delete",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "practitioner_role:create",
    "practitioner_role:read",
    "related_person:create",
    "related_person:read",
    "organization:create",
    "organization:read",
    "encounter:create",
    "encounter:read",
    "appointment:create",
    "appointment:read",
    "location:create",
    "location:read",
    "healthcare_service:create",
    "healthcare_service:read",
    "schedule:create",
    "schedule:read",
    "slot:create",
    "slot:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=CONDITION_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()


@pytest.fixture(autouse=True)
async def _seeded_observations(_set_permissions, client):
    """The Observation ids these tests refer to (`Observation/160001`, ...) must exist."""
    await seed_observations(client)


@pytest.fixture(autouse=True)
async def _seeded_groups(_set_permissions, client):
    """The Group ids these tests refer to (`Group/430001`) must exist."""
    await seed_groups(client)
