import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.episodes_of_care import seed_episodes_of_care
from tests.helpers.groups import seed_groups
from tests.helpers.observations import seed_observations
from tests.helpers.service_requests import seed_service_requests

# The encounter's own scopes, plus the scopes the tests need to create the
# resources it points at (patient, practitioner, location, organization,
# appointment, ...).
ENCOUNTER_PERMS = [
    "episode_of_care:create",
    "episode_of_care:read",
    "group:create",
    "group:read",
    "service_request:create",
    "service_request:read",
    "observation:create",
    "observation:read",
    "condition:create",
    "condition:read",
    "related_person:create",
    "related_person:read",
    "encounter:create",
    "encounter:read",
    "encounter:update",
    "encounter:delete",
    "appointment:create",
    "appointment:read",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "practitioner_role:create",
    "practitioner_role:read",
    "healthcare_service:create",
    "healthcare_service:read",
    "location:create",
    "location:read",
    "organization:create",
    "organization:read",
    "schedule:create",
    "schedule:read",
    "slot:create",
    "slot:read",
    "appointment_response:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=ENCOUNTER_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()


@pytest.fixture(autouse=True)
async def _seeded_observations(_set_permissions, client):
    """The Observation ids these tests refer to (`Observation/160001`, ...) must exist."""
    await seed_observations(client)


@pytest.fixture(autouse=True)
async def _seeded_service_requests(_set_permissions, client):
    """The ServiceRequest ids these tests refer to (`ServiceRequest/80001`, ...) must exist."""
    await seed_service_requests(client)


@pytest.fixture(autouse=True)
async def _seeded_groups(_set_permissions, client):
    """The Group ids these tests refer to (`Group/430001`) must exist."""
    await seed_groups(client)


@pytest.fixture(autouse=True)
async def _seeded_episodes_of_care(_set_permissions, client):
    """The EpisodeOfCare ids these tests refer to (`EpisodeOfCare/350001`) must exist."""
    await seed_episodes_of_care(client)
