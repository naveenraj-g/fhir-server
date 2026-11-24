"""Shared helpers and payloads for measure-report integration tests.

Request bodies are genuine FHIR R4 MeasureReport JSON (camelCase, nested datatypes), and every
response is FHIR R4 too."""

from tests.integration.group.support import create_group, group_body  # noqa: F401
from tests.integration.measure.support import (  # noqa: F401
    create_measure,
    measure_body,
)
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_organization,
    create_practitioner,
)

BASE = "/api/fhir/v1/measure-reports"
API = "/api/fhir/v1"

MEASURE_REPORT_IDS = "https://fhir-server.dev/fhir/identifier-system/measure-report-id"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
MEASURE_URL = "https://fhir-server.dev/fhir/Measure/readmission"
POPULATION = "http://terminology.hl7.org/CodeSystem/measure-population"
PERIOD = {"start": "2026-01-01", "end": "2026-01-31"}


def measure_report_body(**extra) -> dict:
    """A valid minimal measure report: R4 requires `status`, `type`, `measure` and `period`."""
    return {
        "status": "complete",
        "type": "summary",
        "measure": MEASURE_URL,
        "period": PERIOD,
        **extra,
    }


def full_body(patient_id: int, organization_id: int) -> dict:
    """Every R4 element, including the group tree no search parameter reads (it must
    round-trip)."""
    return measure_report_body(
        resourceType="MeasureReport",
        identifier=[
            {
                "system": MEASURE_REPORT_IDS,
                "value": "MR-1001",
                "type": {"coding": [{"system": V2_0203, "code": "ACSN"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        status="complete",
        type="individual",
        measure=f"{MEASURE_URL}|1.0",
        subject={"reference": f"Patient/{patient_id}"},
        date="2026-02-01T10:00:00Z",
        reporter={"reference": f"Organization/{organization_id}"},
        period={"start": "2026-01-01", "end": "2026-01-31"},
        improvementNotation={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/measure-improvement-notation",
                    "code": "increase",
                }
            ]
        },
        group=[
            {
                "id": "g1",
                "code": {"text": "overall"},
                "population": [
                    {
                        "code": {
                            "coding": [
                                {"system": POPULATION, "code": "initial-population"}
                            ]
                        },
                        "count": 120,
                        "subjectResults": {"reference": "List/1"},
                    },
                    {
                        "code": {
                            "coding": [{"system": POPULATION, "code": "numerator"}]
                        },
                        "count": 18,
                    },
                ],
                "measureScore": {"value": 0.15, "unit": "1"},
                "stratifier": [
                    {
                        "code": [{"text": "age"}, {"text": "sex"}],
                        "stratum": [
                            {
                                "value": {"text": "adult"},
                                "population": [
                                    {
                                        "code": {
                                            "coding": [
                                                {
                                                    "system": POPULATION,
                                                    "code": "numerator",
                                                }
                                            ]
                                        },
                                        "count": 7,
                                    }
                                ],
                                "measureScore": {"value": 0.1},
                            },
                            {
                                "component": [
                                    {
                                        "code": {"text": "sex"},
                                        "value": {"text": "female"},
                                    },
                                    {"code": {"text": "ward"}, "value": {"text": "A"}},
                                ],
                                "measureScore": {"value": 0.2},
                            },
                        ],
                    }
                ],
            },
            {"code": {"text": "second"}},
        ],
        evaluatedResource=[
            {"reference": f"Patient/{patient_id}"},
            {"reference": "Device/9"},
        ],
    )


async def create_measure_report(client, body: dict) -> int:
    """Create a measure report and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
