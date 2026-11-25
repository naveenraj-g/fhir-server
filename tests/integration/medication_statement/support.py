"""Shared helpers and payloads for medication statement integration tests.

Request bodies are genuine FHIR R4 MedicationStatement JSON (camelCase, nested datatypes), and
every response is FHIR R4 too."""

# The resources a MedicationStatement points at (and that point back at it) are created through
# their own routers.
from tests.integration.condition.support import (
    condition_body,
    create_condition,
)
from tests.integration.encounter.support import (
    create_encounter,
    encounter_body,
)
from tests.integration.episode_of_care.support import (
    create_episode,
    episode_body,
)
from tests.integration.group.support import create_group, group_body
from tests.integration.medication.support import (
    create_medication,
    medication_body,
)
from tests.integration.observation.support import (
    create_observation,
    observation_body,
)
from tests.integration.patient.support import create_patient
from tests.integration.practitioner_role.support import (
    create_organization,
    create_practitioner,
)
from tests.integration.practitioner_role.support import (
    create_role as create_practitioner_role,
)
from tests.integration.procedure.support import (
    create_procedure,
    procedure_body,
)
from tests.integration.related_person.support import (
    create_related_person,
    related_person_body,
)

BASE = "/api/fhir/v1/medication-statements"
API = "/api/fhir/v1"

STATEMENT_IDS = "https://fhir-server.dev/fhir/identifier-system/medication-statement-id"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
SCT = "http://snomed.info/sct"
UCUM = "http://unitsofmeasure.org"
CATEGORY = "http://terminology.hl7.org/CodeSystem/medication-statement-category"
STATUS_SYSTEM = "http://hl7.org/fhir/CodeSystem/medication-statement-status"
EXTERNAL_PATIENT = {"reference": "https://other.example.org/fhir/Patient/1"}


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


def medication_statement_body(
    patient_id: int | None = None, status: str = "active", **extra
) -> dict:
    """A valid minimal statement: R4 requires `status`, `medication[x]` and `subject`. With no
    patient the subject is an absolute URL (not existence-checked)."""
    subject = (
        {"reference": f"Patient/{patient_id}"} if patient_id else dict(EXTERNAL_PATIENT)
    )
    body = {
        "status": status,
        "medicationCodeableConcept": {"text": "Aspirin"},
        "subject": subject,
    }
    body.update(extra)
    return body


def full_body(
    organization_id: int,
    patient_id: int,
    practitioner_id: int,
    encounter_id: int,
    observation_id: int,
    condition_id: int,
    medication_id: int | None = None,
) -> dict:
    """Every R4 element (the medication as a CodeableConcept unless a medication id is given,
    then as a Reference): all of it must round-trip, indexed or not."""
    body = medication_statement_body(
        patient_id,
        status="completed",
        resourceType="MedicationStatement",
        identifier=[
            {
                "system": STATEMENT_IDS,
                "value": "MS-1001",
                "type": {
                    "coding": [{"system": V2_0203, "code": "RXN"}],
                    "text": "Rx number",
                },
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        basedOn=[{"reference": "https://other.example.org/fhir/ServiceRequest/9"}],
        partOf=[{"reference": f"Observation/{observation_id}"}],
        statusReason=[concept(SCT, "422587007", "Nausea")],
        category=concept(CATEGORY, "community"),
        context={"reference": f"Encounter/{encounter_id}"},
        effectivePeriod={"start": "2026-01-01", "end": "2026-03-01"},
        dateAsserted="2026-01-15T10:05:00Z",
        informationSource={"reference": f"Practitioner/{practitioner_id}"},
        derivedFrom=[
            {"reference": "https://other.example.org/fhir/DocumentReference/9"}
        ],
        reasonCode=[concept(SCT, "38341003", "Hypertension")],
        reasonReference=[{"reference": f"Condition/{condition_id}"}],
        note=[
            {
                "authorReference": {"reference": f"Practitioner/{practitioner_id}"},
                "time": "2026-01-15T10:06:00Z",
                "text": "Takes it in the morning",
            },
            {"authorString": "the patient", "text": "Plain author"},
        ],
        dosage=[
            {
                "sequence": 1,
                "text": "5 mg once daily",
                "additionalInstruction": [concept(SCT, "311504000", "With food")],
                "patientInstruction": "With water",
                "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                "asNeededBoolean": False,
                "route": concept(SCT, "26643006", "Oral"),
                "doseAndRate": [
                    {
                        "doseQuantity": {
                            "value": 5,
                            "unit": "mg",
                            "system": UCUM,
                            "code": "mg",
                        }
                    }
                ],
                "maxDosePerAdministration": {
                    "value": 10,
                    "unit": "mg",
                    "system": UCUM,
                    "code": "mg",
                },
            }
        ],
    )
    if medication_id:
        del body["medicationCodeableConcept"]
        body["medicationReference"] = {"reference": f"Medication/{medication_id}"}
    else:
        body["medicationCodeableConcept"] = concept(
            RXNORM, "197361", "Amlodipine 5 MG Oral Tablet"
        )
    return body


async def create_medication_statement(client, body: dict) -> int:
    """Create a medication statement and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
