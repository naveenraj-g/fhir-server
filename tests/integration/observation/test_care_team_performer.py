"""A CareTeam as a Observation performer: existence-checked on write, searched, chained
(`<param>:CareTeam.status=`), `_include`d and `_revinclude`d from the CareTeam."""

import pytest

from tests.helpers.care_teams import exercise_care_team_performer
from tests.integration.observation.support import API, observation_body
from tests.integration.patient.support import create_patient


@pytest.fixture
async def patient(client) -> int:
    return await create_patient(client)


async def test_care_team_performer_is_followed(client, patient):
    await exercise_care_team_performer(
        client,
        route=f"{API}/observations",
        rtype="Observation",
        param="performer",
        body_with=lambda ref: observation_body(patient, performer=[{"reference": ref}]),
    )
