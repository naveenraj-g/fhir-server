"""A CareTeam as a MedicationRequest performer: existence-checked on write, searched, chained
(`<param>:CareTeam.status=`), `_include`d and `_revinclude`d from the CareTeam."""

import pytest

from tests.helpers.care_teams import exercise_care_team_performer
from tests.integration.medication_request.support import API, medication_request_body
from tests.integration.patient.support import create_patient


@pytest.fixture
async def patient(client) -> int:
    return await create_patient(client)


async def test_care_team_performer_is_followed(client, patient):
    await exercise_care_team_performer(
        client,
        route=f"{API}/medication-requests",
        rtype="MedicationRequest",
        param="intended-performer",
        body_with=lambda ref: medication_request_body(
            patient, performer={"reference": ref}
        ),
    )
