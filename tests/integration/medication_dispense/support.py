"""Shared helpers and payloads for medication dispense integration tests.

Request bodies are genuine FHIR R4 MedicationDispense JSON (camelCase, nested datatypes), and
every response is FHIR R4 too."""

# The resources a MedicationDispense points at (and that point back at it) are created through
# their own routers.
from tests.integration.condition.support import (  # noqa: F401
    condition_body,
    create_condition,
)
from tests.integration.encounter.support import (  # noqa: F401
    create_encounter,
    encounter_body,
)
from tests.integration.episode_of_care.support import (  # noqa: F401
    create_episode,
    episode_body,
)
from tests.integration.group.support import create_group, group_body  # noqa: F401
from tests.integration.medication.support import (  # noqa: F401
    create_medication,
    medication_body,
)
from tests.integration.medication_request.support import (  # noqa: F401
    create_medication_request,
    medication_request_body,
)
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
from tests.integration.procedure.support import (  # noqa: F401
    create_procedure,
    procedure_body,
)
from tests.integration.related_person.support import (  # noqa: F401
    create_related_person,
    related_person_body,
)

BASE = "/api/fhir/v1/medication-dispenses"
API = "/api/fhir/v1"

DISPENSE_IDS = "https://fhir-server.dev/fhir/identifier-system/medication-dispense-id"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
SCT = "http://snomed.info/sct"
UCUM = "http://unitsofmeasure.org"
ACT_CODE = "http://terminology.hl7.org/CodeSystem/v3-ActCode"
CATEGORY = "http://terminology.hl7.org/CodeSystem/medicationdispense-category"
STATUS_SYSTEM = "http://hl7.org/fhir/CodeSystem/medicationdispense-status"
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


def medication_dispense_body(
    patient_id: int | None = None, status: str = "completed", **extra
) -> dict:
    """A valid minimal dispense: R4 requires `status` and `medication[x]`. With no patient the
    subject is an absolute URL (not existence-checked)."""
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
    request_id: int,
    location_id: int,
    medication_id: int | None = None,
) -> dict:
    """Every R4 element (the medication as a CodeableConcept unless a medication id is given,
    then as a Reference): all of it must round-trip, indexed or not."""
    body = medication_dispense_body(
        patient_id,
        status="completed",
        resourceType="MedicationDispense",
        identifier=[
            {
                "system": DISPENSE_IDS,
                "value": "MD-1001",
                "type": {
                    "coding": [{"system": V2_0203, "code": "DSP"}],
                    "text": "Dispense number",
                },
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        statusReasonCodeableConcept=concept(SCT, "418309008", "Out of stock"),
        category=concept(CATEGORY, "outpatient"),
        context={"reference": f"Encounter/{encounter_id}"},
        supportingInformation=[{"reference": f"Observation/{observation_id}"}],
        performer=[
            {
                "function": concept(
                    "http://terminology.hl7.org/CodeSystem/medicationdispense-performer-function",
                    "packager",
                ),
                "actor": {"reference": f"Practitioner/{practitioner_id}"},
            },
            {"actor": {"reference": "https://other.example.org/fhir/Device/9"}},
        ],
        location={"reference": f"Location/{location_id}"},
        authorizingPrescription=[{"reference": f"MedicationRequest/{request_id}"}],
        type=concept(ACT_CODE, "FF", "First Fill"),
        quantity={"value": 30, "unit": "tablet"},
        daysSupply={"value": 30, "unit": "Day", "system": UCUM, "code": "d"},
        whenPrepared="2026-01-15T09:00:00Z",
        whenHandedOver="2026-01-15T10:00:00Z",
        destination={"reference": f"Location/{location_id}"},
        receiver=[{"reference": f"Patient/{patient_id}"}],
        note=[
            {
                "authorReference": {"reference": f"Practitioner/{practitioner_id}"},
                "time": "2026-01-15T10:05:00Z",
                "text": "Counselled",
            },
            {"authorString": "the pharmacist", "text": "Plain author"},
        ],
        dosageInstruction=[
            {
                "sequence": 1,
                "text": "1 tablet daily",
                "route": concept(SCT, "26643006", "Oral"),
                "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                "doseAndRate": [
                    {"doseQuantity": {"value": 1, "unit": "tablet"}},
                ],
            }
        ],
        substitution={
            "wasSubstituted": True,
            "type": concept(
                "http://terminology.hl7.org/CodeSystem/v3-ActSubstanceAdminSubstitutionCode",
                "E",
            ),
            "reason": [
                concept("http://terminology.hl7.org/CodeSystem/v3-ActReason", "FP")
            ],
            "responsibleParty": [{"reference": f"Practitioner/{practitioner_id}"}],
        },
        eventHistory=[{"reference": "https://other.example.org/fhir/Provenance/1"}],
    )
    if medication_id:
        del body["medicationCodeableConcept"]
        body["medicationReference"] = {"reference": f"Medication/{medication_id}"}
    else:
        body["medicationCodeableConcept"] = concept(
            RXNORM, "197361", "Amlodipine 5 MG Oral Tablet"
        )
    return body


async def create_medication_dispense(client, body: dict) -> int:
    """Create a medication dispense and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
