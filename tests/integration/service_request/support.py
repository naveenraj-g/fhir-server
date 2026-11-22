"""Shared helpers and payloads for service request integration tests.

Request bodies are genuine FHIR R4 ServiceRequest JSON (camelCase, nested datatypes), and every
response is FHIR R4 too."""

# The resources a ServiceRequest points at (and that point back at it) are created through their
# own routers.
from tests.integration.appointment.support import (  # noqa: F401
    appointment_body,
    create_appointment,
    create_condition,
)
from tests.integration.diagnostic_report.support import (  # noqa: F401
    create_report,
    report_body,
)
from tests.integration.encounter.support import (  # noqa: F401
    create_encounter,
    encounter_body,
)
from tests.integration.observation.support import (  # noqa: F401
    create_observation,
    observation_body,
)
from tests.integration.patient.support import create_patient  # noqa: F401
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_healthcare_service,
    create_location,
    create_organization,
    create_practitioner,
    create_role as create_practitioner_role,
)
from tests.integration.related_person.support import (  # noqa: F401
    create_related_person,
    related_person_body,
)
from tests.integration.specimen.support import create_specimen, specimen_body  # noqa: F401

BASE = "/api/fhir/v1/service-requests"
API = "/api/fhir/v1"

ORDER_IDS = "https://fhir-server.dev/fhir/identifier-system/service-request-id"
REQUISITIONS = "http://lab.example.org/requisitions"
REQUEST_STATUS = "http://hl7.org/fhir/request-status"
REQUEST_INTENT = "http://hl7.org/fhir/request-intent"
REQUEST_PRIORITY = "http://hl7.org/fhir/request-priority"
SCT = "http://snomed.info/sct"
LOINC = "http://loinc.org"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
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


def service_request_body(
    patient_id: int | None = None,
    status: str = "active",
    intent: str = "order",
    **extra,
) -> dict:
    """A valid minimal ServiceRequest: R4 requires `status`, `intent` and `subject`. With no
    patient the subject is an absolute URL (not existence-checked)."""
    subject = {
        "reference": f"Patient/{patient_id}"
        if patient_id
        else "https://other.example.org/fhir/Patient/1"
    }
    return {"status": status, "intent": intent, "subject": subject, **extra}


def full_body(
    patient_id: int,
    encounter_id: int,
    practitioner_id: int,
    organization_id: int,
    location_id: int,
    specimen_id: int,
    based_on_id: int,
    replaces_id: int,
    condition_id: int,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return service_request_body(
        patient_id,
        resourceType="ServiceRequest",
        identifier=[
            {
                "system": ORDER_IDS,
                "value": "SR-1001",
                "type": {"coding": [{"system": V2_0203, "code": "PLAC"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        instantiatesCanonical=["http://example.org/fhir/PlanDefinition/cbc|1.0"],
        instantiatesUri=["http://example.org/protocols/cbc"],
        basedOn=[{"reference": f"ServiceRequest/{based_on_id}"}],
        replaces=[{"reference": f"ServiceRequest/{replaces_id}"}],
        requisition={
            "system": REQUISITIONS,
            "value": "RQ-1",
            "assigner": {"reference": f"Organization/{organization_id}"},
        },
        category=[concept(SCT, "108252007", "Laboratory procedure")],
        priority="urgent",
        doNotPerform=False,
        code=concept(LOINC, "58410-2", "CBC panel"),
        orderDetail=[concept(SCT, "1", "Detail")],
        quantityQuantity={"value": 2, "unit": "mL", "system": UCUM, "code": "mL"},
        encounter={"reference": f"Encounter/{encounter_id}"},
        occurrenceDateTime="2023-01-16T09:00:00Z",
        asNeededBoolean=True,
        authoredOn="2023-01-15T09:30:00Z",
        requester={"reference": f"Practitioner/{practitioner_id}"},
        performerType=concept(SCT, "309343006", "Physician"),
        performer=[{"reference": f"Organization/{organization_id}"}],
        locationCode=[concept(SCT, "1", "Loc")],
        locationReference=[{"reference": f"Location/{location_id}"}],
        reasonCode=[concept(SCT, "271737000", "Anemia")],
        reasonReference=[{"reference": f"Condition/{condition_id}"}],
        insurance=[{"reference": "Coverage/240001"}],
        supportingInfo=[{"reference": f"Patient/{patient_id}"}],
        specimen=[{"reference": f"Specimen/{specimen_id}"}],
        bodySite=[concept(SCT, "368208006", "Left upper arm structure")],
        note=[{"text": "Fasting not required.", "authorString": "Nurse Joy"}],
        patientInstruction="Drink water.",
        relevantHistory=[{"reference": "Provenance/270001"}],
    )


async def create_service_request(client, body: dict) -> int:
    """Create a service request and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
