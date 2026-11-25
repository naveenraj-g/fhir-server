"""Shared helpers and payloads for consent integration tests.

Request bodies are genuine FHIR R4 Consent JSON (camelCase, nested datatypes), and every response is
FHIR R4 too."""

from tests.integration.care_team.support import (
    care_team_body,
    create_care_team,
)
from tests.integration.document_reference.support import (
    create_document,
    document_body,
)
from tests.integration.group.support import create_group, group_body
from tests.integration.observation.support import (
    create_observation,
    observation_body,
)
from tests.integration.patient.support import create_patient
from tests.integration.practitioner_role.support import (
    create_organization,
    create_practitioner,
)
from tests.integration.related_person.support import (
    create_related_person,
    related_person_body,
)

BASE = "/api/fhir/v1/consents"
API = "/api/fhir/v1"

CONSENT_IDS = "https://fhir-server.dev/fhir/identifier-system/consent-id"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
SCOPE = "http://terminology.hl7.org/CodeSystem/consentscope"
LOINC = "http://loinc.org"
ACTION = "http://terminology.hl7.org/CodeSystem/consentaction"
PURPOSE = "http://terminology.hl7.org/CodeSystem/v3-ActReason"
CONFIDENTIALITY = "http://terminology.hl7.org/CodeSystem/v3-Confidentiality"
ROLE = "http://terminology.hl7.org/CodeSystem/v3-ParticipationType"


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


def consent_body(patient_id: int | None = None, **extra) -> dict:
    """A valid minimal Consent: R4 requires `status`, `scope` and `category`. With no patient the
    `patient` element is omitted."""
    body = {
        "status": "active",
        "scope": concept(SCOPE, "patient-privacy"),
        "category": [concept(LOINC, "59284-0")],
        **extra,
    }
    if patient_id:
        body["patient"] = {"reference": f"Patient/{patient_id}"}
    return body


def full_body(
    patient_id: int,
    organization_id: int,
    practitioner_id: int,
    document_id: int,
    observation_id: int,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return consent_body(
        patient_id,
        resourceType="Consent",
        identifier=[
            {
                "system": CONSENT_IDS,
                "value": "C-1001",
                "type": {"coding": [{"system": V2_0203, "code": "FILL"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        dateTime="2026-01-15T09:00:00Z",
        performer=[{"reference": f"Patient/{patient_id}"}],
        organization=[{"reference": f"Organization/{organization_id}"}],
        sourceReference={"reference": f"DocumentReference/{document_id}"},
        policy=[{"authority": "urn:authority", "uri": "http://example.org/policy"}],
        policyRule=concept("http://terminology.hl7.org/CodeSystem/v3-ActCode", "OPTIN"),
        verification=[
            {
                "verified": True,
                "verifiedWith": {"reference": f"Patient/{patient_id}"},
                "verificationDate": "2026-01-16T10:00:00Z",
            }
        ],
        provision={
            "type": "permit",
            "period": {"start": "2026-01-15", "end": "2027-01-14"},
            "actor": [
                {
                    "role": concept(ROLE, "IRCP"),
                    "reference": {"reference": f"Practitioner/{practitioner_id}"},
                }
            ],
            "action": [concept(ACTION, "access")],
            "securityLabel": [{"system": CONFIDENTIALITY, "code": "R"}],
            "purpose": [{"system": PURPOSE, "code": "TREAT"}],
            "class": [
                {"system": "http://hl7.org/fhir/resource-types", "code": "Observation"}
            ],
            "code": [concept(LOINC, "8867-4")],
            "dataPeriod": {"start": "2025-01-01", "end": "2025-12-31"},
            "data": [
                {
                    "meaning": "instance",
                    "reference": {"reference": f"Observation/{observation_id}"},
                }
            ],
            "provision": [
                {
                    "type": "deny",
                    "action": [concept(ACTION, "disclose")],
                    "actor": [
                        {
                            "role": concept(ROLE, "IRCP"),
                            "reference": {
                                "reference": f"Organization/{organization_id}"
                            },
                        }
                    ],
                }
            ],
        },
    )


async def create_consent(client, body: dict) -> int:
    """Create a consent and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
