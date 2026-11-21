"""Shared helpers and payloads for observation integration tests.

Request bodies are genuine FHIR R4 Observation JSON (camelCase, nested datatypes), and every
response is FHIR R4 too."""

# The resources an Observation points at (and that point back at it) are created through their
# own routers.
from tests.integration.encounter.support import create_encounter, encounter_body  # noqa: F401
from tests.integration.immunization.support import (
    create_immunization,
    immunization_body,
)  # noqa: F401
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_location,
    create_organization,
    create_practitioner,
    create_role as create_practitioner_role,
)
from tests.integration.procedure.support import create_procedure, procedure_body  # noqa: F401
from tests.integration.related_person.support import (
    create_related_person,
    related_person_body,
)  # noqa: F401

BASE = "/api/fhir/v1/observations"
API = "/api/fhir/v1"

OBSERVATION_IDS = "https://fhir-server.dev/fhir/identifier-system/observation-id"
LOINC = "http://loinc.org"
SCT = "http://snomed.info/sct"
UCUM = "http://unitsofmeasure.org"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
CATEGORY = "http://terminology.hl7.org/CodeSystem/observation-category"
INTERPRETATION = "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"


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


def loinc(code: str, display: str | None = None) -> dict:
    return concept(LOINC, code, display)


def quantity(value: float | int, unit: str = "mmHg", code: str = "mm[Hg]") -> dict:
    return {"value": value, "unit": unit, "system": UCUM, "code": code}


def observation_body(
    patient_id: int | None = None, status: str = "final", **extra
) -> dict:
    """A valid minimal Observation: R4 requires `status` and `code`. With no patient the `subject`
    element is omitted."""
    body = {"status": status, "code": {"text": "Observation"}, **extra}
    if patient_id:
        body["subject"] = {"reference": f"Patient/{patient_id}"}
    return body


def blood_pressure(
    patient_id: int | None, systolic: float | int, diastolic: float | int, **extra
) -> dict:
    """A blood-pressure panel: the panel code with a systolic and a diastolic component."""
    return observation_body(
        patient_id,
        category=[concept(CATEGORY, "vital-signs", "Vital Signs")],
        code=loinc("85354-9", "Blood pressure panel"),
        component=[
            {
                "code": loinc("8480-6", "Systolic blood pressure"),
                "valueQuantity": quantity(systolic),
            },
            {
                "code": loinc("8462-4", "Diastolic blood pressure"),
                "valueQuantity": quantity(diastolic),
            },
        ],
        **extra,
    )


def full_body(
    patient_id: int,
    encounter_id: int,
    practitioner_id: int,
    organization_id: int,
    member_id: int,
    procedure_id: int,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return observation_body(
        patient_id,
        resourceType="Observation",
        identifier=[
            {
                "system": OBSERVATION_IDS,
                "value": "OBS-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        basedOn=[{"reference": "ServiceRequest/80001"}],
        partOf=[{"reference": f"Procedure/{procedure_id}"}],
        category=[concept(CATEGORY, "vital-signs", "Vital Signs")],
        code=loinc("85354-9", "Blood pressure panel"),
        focus=[{"reference": "Condition/999999"}],
        encounter={"reference": f"Encounter/{encounter_id}"},
        effectiveDateTime="2023-01-15T09:30:00Z",
        issued="2023-01-15T09:35:00Z",
        performer=[{"reference": f"Practitioner/{practitioner_id}"}],
        valueQuantity=quantity(120),
        interpretation=[concept(INTERPRETATION, "H", "High")],
        note=[
            {
                "text": "Taken seated.",
                "time": "2023-01-15T09:31:00Z",
                "authorString": "Nurse Joy",
            }
        ],
        bodySite=concept(SCT, "368208006", "Left upper arm structure"),
        method=concept(SCT, "37931006", "Auscultation"),
        specimen={"reference": "https://other.example.org/fhir/Specimen/3"},
        device={"reference": "Device/5"},
        referenceRange=[
            {
                "low": quantity(90),
                "high": quantity(140),
                "type": concept(
                    "http://terminology.hl7.org/CodeSystem/referencerange-meaning",
                    "normal",
                ),
                "appliesTo": [{"text": "Adults"}],
                "age": {
                    "low": {"value": 18, "unit": "yr", "system": UCUM, "code": "a"}
                },
                "text": "90-140 mmHg",
            }
        ],
        hasMember=[{"reference": f"Observation/{member_id}"}],
        derivedFrom=[{"reference": "Media/7"}],
        component=[
            {
                "code": loinc("8480-6", "Systolic blood pressure"),
                "valueQuantity": quantity(142),
                "interpretation": [concept(INTERPRETATION, "H")],
                "referenceRange": [{"high": quantity(140)}],
            },
            {
                "code": loinc("8462-4", "Diastolic blood pressure"),
                "dataAbsentReason": concept(
                    "http://terminology.hl7.org/CodeSystem/data-absent-reason",
                    "unknown",
                ),
            },
        ],
    )


async def create_observation(client, body: dict) -> int:
    """Create an observation and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
