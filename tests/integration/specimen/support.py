"""Shared helpers and payloads for specimen integration tests.

Request bodies are genuine FHIR R4 Specimen JSON (camelCase, nested datatypes), and every
response is FHIR R4 too."""

# The resources a Specimen points at (and that point back at it) are created through their own
# routers.
from tests.integration.observation.support import (  # noqa: F401
    create_observation,
    observation_body,
)
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_location,
    create_organization,
    create_practitioner,
    create_role as create_practitioner_role,
)

BASE = "/api/fhir/v1/specimens"
API = "/api/fhir/v1"

SPECIMEN_IDS = "https://fhir-server.dev/fhir/identifier-system/specimen-id"
ACCESSIONS = "http://lab.example.org/accessions"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
V2_0487 = "http://terminology.hl7.org/CodeSystem/v2-0487"
SCT = "http://snomed.info/sct"
UCUM = "http://unitsofmeasure.org"


def concept(system: str, code: str, display: str | None = None) -> dict:
    return {
        "coding": [
            {
                "system": system,
                "code": code,
                **({"display": display} if display else {}),
            }
        ]
    }


def specimen_body(patient_id: int | None = None, **extra) -> dict:
    """A valid minimal Specimen (every R4 element is optional). With a patient the `subject` is set."""
    body = dict(extra)
    if patient_id:
        body["subject"] = {"reference": f"Patient/{patient_id}"}
    return body


def full_body(
    patient_id: int,
    practitioner_id: int,
    organization_id: int,
    parent_id: int,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return specimen_body(
        patient_id,
        resourceType="Specimen",
        identifier=[
            {
                "system": SPECIMEN_IDS,
                "value": "SP-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        accessionIdentifier={
            "system": ACCESSIONS,
            "value": "ACC-1",
            "assigner": {"reference": f"Organization/{organization_id}"},
        },
        status="available",
        type=concept(V2_0487, "BLD", "Whole blood"),
        receivedTime="2023-01-15T11:00:00Z",
        parent=[{"reference": f"Specimen/{parent_id}"}],
        request=[{"reference": "ServiceRequest/80001"}],
        collection={
            "collector": {"reference": f"Practitioner/{practitioner_id}"},
            "collectedDateTime": "2023-01-15T09:30:00Z",
            "duration": {"value": 5, "unit": "min", "system": UCUM, "code": "min"},
            "quantity": {"value": 6, "unit": "mL", "system": UCUM, "code": "mL"},
            "method": concept(SCT, "82078001", "Collection of blood specimen"),
            "bodySite": concept(SCT, "368208006", "Left upper arm structure"),
            "fastingStatusCodeableConcept": concept(
                "http://terminology.hl7.org/CodeSystem/v2-0916",
                "F",
                "Patient was fasting",
            ),
        },
        processing=[
            {
                "description": "Centrifuged",
                "procedure": concept(SCT, "9265001", "Specimen centrifugation"),
                "additive": [{"reference": "Substance/1"}],
                "timeDateTime": "2023-01-15T11:30:00Z",
            }
        ],
        container=[
            {
                "identifier": [{"system": "urn:containers", "value": "C-1"}],
                "description": "Red top tube",
                "type": concept(SCT, "434746001", "Specimen vial"),
                "capacity": {"value": 10, "unit": "mL", "system": UCUM, "code": "mL"},
                "specimenQuantity": {
                    "value": 6,
                    "unit": "mL",
                    "system": UCUM,
                    "code": "mL",
                },
                "additiveCodeableConcept": concept(SCT, "118424005", "Heparin"),
            }
        ],
        condition=[
            concept("http://terminology.hl7.org/CodeSystem/v2-0493", "HEM", "Hemolyzed")
        ],
        note=[
            {
                "text": "Fasting sample.",
                "time": "2023-01-15T09:31:00Z",
                "authorString": "Nurse Joy",
            }
        ],
    )


async def create_specimen(client, body: dict) -> int:
    """Create a specimen and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
