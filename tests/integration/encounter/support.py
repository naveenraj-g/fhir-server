"""Shared helpers and payloads for encounter integration tests.

Request bodies are genuine FHIR R4 Encounter JSON (camelCase, nested
datatypes), and every response is FHIR R4 too."""

# The resources an Encounter points at are created through their own routers.
from tests.integration.appointment.support import (  # noqa: F401
    appointment_body,
    create_appointment,
    create_condition,
    create_healthcare_service,
    create_location,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    participant,
)

BASE = "/api/fhir/v1/encounters"
API = "/api/fhir/v1"

ENC_IDS = "https://fhir-server.dev/fhir/identifier-system/encounter-id"
ACT = "http://terminology.hl7.org/CodeSystem/v3-ActCode"
PART = "http://terminology.hl7.org/CodeSystem/v3-ParticipationType"
SPECIAL = "http://terminology.hl7.org/CodeSystem/v3-EncounterSpecialCourtesy"
SCT = "http://snomed.info/sct"
UCUM = "http://unitsofmeasure.org"

START = "2026-06-01T09:00:00Z"
END = "2026-06-01T09:40:00Z"


def cls(code: str = "AMB") -> dict:
    """Encounter.class is a bare Coding (not a CodeableConcept)."""
    return {"system": ACT, "code": code}


def encounter_body(
    status: str = "in-progress", class_code: str = "AMB", **extra
) -> dict:
    """A valid minimal Encounter: R4 requires `status` and `class`."""
    return {"status": status, "class": cls(class_code), **extra}


def full_body(
    patient_id: int,
    practitioner_id: int,
    location_id: int,
    organization_id: int,
    appointment_id: int,
    condition_id: int,
) -> dict:
    return encounter_body(
        resourceType="Encounter",
        identifier=[
            {
                "system": ENC_IDS,
                "value": "E-1001",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "VN",
                        }
                    ]
                },
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        statusHistory=[
            {
                "status": "planned",
                "period": {"start": "2026-05-30T08:00:00Z", "end": START},
            }
        ],
        classHistory=[
            {
                "class": cls("IMP"),
                "period": {"start": "2026-05-30T08:00:00Z", "end": START},
            }
        ],
        type=[
            {
                "coding": [
                    {
                        "system": SCT,
                        "code": "270427003",
                        "display": "Patient-initiated encounter",
                    }
                ],
                "text": "Initial",
            }
        ],
        serviceType={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/service-type",
                    "code": "124",
                }
            ]
        },
        priority={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActPriority",
                    "code": "R",
                }
            ]
        },
        subject={"reference": f"Patient/{patient_id}", "display": "A. Patient"},
        episodeOfCare=[{"reference": "EpisodeOfCare/350001"}],
        basedOn=[{"reference": "ServiceRequest/80001"}],
        participant=[
            {
                "type": [
                    {"coding": [{"system": PART, "code": "ATND"}], "text": "attender"}
                ],
                "period": {"start": START},
                "individual": {"reference": f"Practitioner/{practitioner_id}"},
            }
        ],
        appointment=[{"reference": f"Appointment/{appointment_id}"}],
        period={"start": START, "end": END},
        length={"value": 40, "unit": "min", "system": UCUM, "code": "min"},
        reasonCode=[
            {"coding": [{"system": SCT, "code": "185347001"}], "text": "Check-up"}
        ],
        reasonReference=[{"reference": f"Condition/{condition_id}"}],
        diagnosis=[
            {
                "condition": {"reference": f"Condition/{condition_id}"},
                "use": {"text": "Admission"},
                "rank": 1,
            }
        ],
        account=[{"reference": "Account/7"}],
        hospitalization={
            "preAdmissionIdentifier": {"system": "urn:pre", "value": "PRE-1"},
            "admitSource": {"text": "Referral"},
            "dietPreference": [{"text": "Vegetarian"}],
            "specialArrangement": [
                {"coding": [{"system": SPECIAL, "code": "wheel"}], "text": "Wheelchair"}
            ],
            "dischargeDisposition": {"text": "Home"},
        },
        location=[
            {
                "location": {"reference": f"Location/{location_id}"},
                "status": "completed",
                "physicalType": {"text": "Room"},
                "period": {"start": START, "end": "2026-06-01T09:30:00Z"},
            }
        ],
        serviceProvider={"reference": f"Organization/{organization_id}"},
    )


async def create_encounter(client, body: dict) -> int:
    """Create an encounter and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
