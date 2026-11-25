"""Shared helpers and payloads for medication request integration tests.

Request bodies are genuine FHIR R4 MedicationRequest JSON (camelCase, nested datatypes), and
every response is FHIR R4 too."""

# The resources a MedicationRequest points at (and that point back at it) are created through
# their own routers.
from tests.integration.appointment.support import create_condition
from tests.integration.encounter.support import (
    create_encounter,
    encounter_body,
)
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
from tests.integration.related_person.support import (
    create_related_person,
    related_person_body,
)

BASE = "/api/fhir/v1/medication-requests"
API = "/api/fhir/v1"

RX_IDS = "https://fhir-server.dev/fhir/identifier-system/prescription-id"
GROUPS = "https://fhir-server.dev/fhir/identifier-system/prescription-group"
RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
SCT = "http://snomed.info/sct"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
CATEGORY = "http://terminology.hl7.org/CodeSystem/medicationrequest-category"


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


def medication_request_body(
    patient_id: int | None = None,
    status: str = "active",
    intent: str = "order",
    **extra,
) -> dict:
    """A valid minimal MedicationRequest: R4 requires `status`, `intent`, `medication[x]` and
    `subject`. With no patient the subject is an absolute URL (not existence-checked)."""
    subject = {
        "reference": f"Patient/{patient_id}"
        if patient_id
        else "https://other.example.org/fhir/Patient/1"
    }
    body = {
        "status": status,
        "intent": intent,
        "medicationCodeableConcept": {"text": "Aspirin"},
        "subject": subject,
    }
    body.update(extra)
    return body


def full_body(
    patient_id: int,
    encounter_id: int,
    practitioner_id: int,
    organization_id: int,
    medication_id: int,
    prior_id: int,
    condition_id: int,
    detected_issue_id: int,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip).
    `medication[x]` is the reference form here."""
    body = medication_request_body(
        patient_id,
        resourceType="MedicationRequest",
        identifier=[
            {
                "system": RX_IDS,
                "value": "RX-1001",
                "type": {"coding": [{"system": V2_0203, "code": "PLAC"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        statusReason=concept(SCT, "1", "Reason"),
        category=[concept(CATEGORY, "outpatient", "Outpatient")],
        priority="urgent",
        doNotPerform=False,
        reportedBoolean=True,
        medicationReference={"reference": f"Medication/{medication_id}"},
        encounter={"reference": f"Encounter/{encounter_id}"},
        supportingInformation=[{"reference": f"Patient/{patient_id}"}],
        authoredOn="2023-01-15T09:30:00Z",
        requester={"reference": f"Practitioner/{practitioner_id}"},
        performer={"reference": f"Organization/{organization_id}"},
        performerType=concept(SCT, "309343006", "Physician"),
        recorder={"reference": f"Practitioner/{practitioner_id}"},
        reasonCode=[concept(SCT, "22253000", "Pain")],
        reasonReference=[{"reference": f"Condition/{condition_id}"}],
        instantiatesCanonical=["http://example.org/fhir/PlanDefinition/pain|1.0"],
        instantiatesUri=["http://example.org/protocols/pain"],
        basedOn=[{"reference": f"MedicationRequest/{prior_id}"}],
        groupIdentifier={"system": GROUPS, "value": "GRP-1"},
        courseOfTherapyType=concept(
            "http://terminology.hl7.org/CodeSystem/medicationrequest-course-of-therapy",
            "continuous",
        ),
        insurance=[{"reference": "Coverage/240001"}],
        note=[{"text": "Take with food.", "authorString": "Nurse Joy"}],
        dosageInstruction=[
            {
                "sequence": 1,
                "text": "1 tablet every 12 hours",
                "timing": {
                    "event": ["2023-01-16T08:00:00Z", "2023-01-16T20:00:00Z"],
                    "repeat": {"frequency": 1, "period": 12, "periodUnit": "h"},
                },
                "route": concept(SCT, "26643006", "Oral route"),
                "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}],
            }
        ],
        dispenseRequest={
            "initialFill": {"quantity": {"value": 30, "unit": "tablet"}},
            "dispenseInterval": {"value": 7, "unit": "days"},
            "validityPeriod": {"start": "2023-01-15", "end": "2023-07-15"},
            "numberOfRepeatsAllowed": 2,
            "quantity": {"value": 60, "unit": "tablet"},
            "expectedSupplyDuration": {"value": 30, "unit": "days"},
            "performer": {"reference": f"Organization/{organization_id}"},
        },
        substitution={"allowedBoolean": True, "reason": concept(SCT, "2", "Cost")},
        priorPrescription={"reference": f"MedicationRequest/{prior_id}"},
        detectedIssue=[{"reference": f"DetectedIssue/{detected_issue_id}"}],
        eventHistory=[{"reference": "Provenance/270001"}],
    )
    del body["medicationCodeableConcept"]
    return body


async def create_medication_request(client, body: dict) -> int:
    """Create a medication request and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def create_detected_issue(client, patient_id: int) -> int:
    resp = await client.post(
        API + "/detected-issues/",
        json={"status": "final", "patient": {"reference": f"Patient/{patient_id}"}},
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
