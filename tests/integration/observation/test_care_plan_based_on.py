"""A CarePlan as the target of Observation.basedOn: existence-checked on write, searched, chained
(`based-on:CarePlan.status=`), `_include`d and `_revinclude`d from the CarePlan."""

import pytest

from tests.helpers.care_plans import exercise_based_on_care_plan
from tests.integration.observation.support import API, observation_body
from tests.integration.patient.support import create_patient


@pytest.fixture
async def patient(client) -> int:
    return await create_patient(client)


async def test_care_plan_based_on_is_followed(client, patient):
    await exercise_based_on_care_plan(
        client,
        route=f"{API}/observations",
        rtype="Observation",
        body_with=lambda based_on: observation_body(patient, basedOn=based_on),
    )
