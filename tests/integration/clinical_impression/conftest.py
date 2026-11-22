import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.groups import seed_groups
from tests.helpers.observations import seed_observations

# The impression's own scopes, plus the scopes the tests need to create the resources around it
# (its subject, encounter, assessor, problems, investigations, findings and note authors) and the ones to look
# at what points back at it.
IMPRESSION_PERMS = [
    "group:create",
    "group:read",
    "observation:create",
    "observation:read",
    "clinical_impression:create",
    "clinical_impression:read",
    "clinical_impression:update",
    "clinical_impression:delete",
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
    "condition:create",
    "condition:read",
    "diagnostic_report:create",
    "diagnostic_report:read",
    "risk_assessment:create",
    "risk_assessment:read",
    "family_member_history:create",
    "family_member_history:read",
    "allergy_intolerance:create",
    "allergy_intolerance:read",
    "related_person:create",
    "related_person:read",
    "location:create",
    "location:read",
    "procedure:create",
    "procedure:read",
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
        permissions=IMPRESSION_PERMS
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
