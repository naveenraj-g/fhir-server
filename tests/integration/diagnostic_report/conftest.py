import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.service_requests import seed_service_requests
from tests.helpers.specimens import seed_specimens
from tests.helpers.observations import seed_observations

# The report's own scopes, plus the scopes the tests need to create the resources
# around it (its subject, encounter, performers, and the procedures / encounters
# that point back at it).
REPORT_PERMS = [
    "care_team:create",
    "care_team:read",
    "care_plan:create",
    "care_plan:read",
    "medication_request:create",
    "medication_request:read",
    "service_request:create",
    "service_request:read",
    "specimen:create",
    "specimen:read",
    "observation:create",
    "observation:read",
    "diagnostic_report:create",
    "diagnostic_report:read",
    "diagnostic_report:update",
    "diagnostic_report:delete",
    "procedure:create",
    "procedure:read",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "practitioner_role:create",
    "practitioner_role:read",
    "organization:create",
    "organization:read",
    "encounter:create",
    "encounter:read",
    "location:create",
    "location:read",
    "condition:create",
    "condition:read",
    "related_person:create",
    "related_person:read",
    "appointment:create",
    "appointment:read",
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
        permissions=REPORT_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()


@pytest.fixture(autouse=True)
async def _seeded_observations(_set_permissions, client):
    """The Observation ids these tests refer to (`Observation/160001`, ...) must exist."""
    await seed_observations(client)


@pytest.fixture(autouse=True)
async def _seeded_specimens(_set_permissions, client):
    """The Specimen ids these tests refer to (`Specimen/310001`, ...) must exist."""
    await seed_specimens(client)


@pytest.fixture(autouse=True)
async def _seeded_service_requests(_set_permissions, client):
    """The ServiceRequest ids these tests refer to (`ServiceRequest/80001`, ...) must exist."""
    await seed_service_requests(client)
