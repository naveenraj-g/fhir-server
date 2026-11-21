import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.specimens import seed_specimens

# The observation's own scopes, plus the scopes the tests need to create the resources around it
# (its subject, encounter, performers, members) and the ones to look at what points back at it.
OBSERVATION_PERMS = [
    "specimen:create",
    "specimen:read",
    "observation:create",
    "observation:read",
    "observation:update",
    "observation:delete",
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
    "clinical_impression:create",
    "clinical_impression:read",
    "related_person:create",
    "related_person:read",
    "location:create",
    "location:read",
    "procedure:create",
    "procedure:read",
    "immunization:create",
    "immunization:read",
    "appointment:create",
    "appointment:read",
    "healthcare_service:create",
    "healthcare_service:read",
    "schedule:create",
    "schedule:read",
    "slot:create",
    "slot:read",
    "detected_issue:create",
    "detected_issue:read",
    "immunization_recommendation:create",
    "immunization_recommendation:read",
]


@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=OBSERVATION_PERMS
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()


@pytest.fixture(autouse=True)
async def _seeded_specimens(_set_permissions, client):
    """The Specimen ids these tests refer to (`Specimen/310001`, ...) must exist."""
    await seed_specimens(client)
