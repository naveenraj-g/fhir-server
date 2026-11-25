import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.observations import seed_observations

# The recommendation's own scopes, plus the scopes the tests need to create the
# resources around it (its patient, authority, supporting immunizations and patient
# information) and the ones to look at what points back at it.
RECOMMENDATION_PERMS = [
    "observation:create",
    "observation:read",
    "immunization_recommendation:create",
    "immunization_recommendation:read",
    "immunization_recommendation:update",
    "immunization_recommendation:delete",
    "immunization_evaluation:create",
    "immunization_evaluation:read",
    "immunization:create",
    "immunization:read",
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
    "diagnostic_report:create",
    "diagnostic_report:read",
    "procedure:create",
    "procedure:read",
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
        permissions=RECOMMENDATION_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()


@pytest.fixture(autouse=True)
async def _seeded_observations(_set_permissions, client):
    """The Observation ids these tests refer to (`Observation/160001`, ...) must exist."""
    await seed_observations(client)
