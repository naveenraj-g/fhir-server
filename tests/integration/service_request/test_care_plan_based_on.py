"""A CarePlan as the target of ServiceRequest.basedOn: existence-checked on write, searched, chained
(`based-on:CarePlan.status=`), `_include`d and `_revinclude`d from the CarePlan."""

import pytest

from tests.helpers.care_plans import exercise_based_on_care_plan
from tests.integration.patient.support import create_patient
from tests.integration.service_request.support import API, service_request_body


@pytest.fixture
async def patient(client) -> int:
    return await create_patient(client)


async def test_care_plan_based_on_is_followed(client, patient):
    await exercise_based_on_care_plan(
        client,
        route=f"{API}/service-requests",
        rtype="ServiceRequest",
        body_with=lambda based_on: service_request_body(patient, basedOn=based_on),
    )
