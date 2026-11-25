"""Shared helpers and payloads for document_reference integration tests.

Request bodies are genuine FHIR R4 DocumentReference JSON (camelCase, nested datatypes), and every
response is FHIR R4 too."""

# The resources a DocumentReference points at (and that point back at it) are created through
# their own routers.
from tests.integration.condition.support import (
    condition_body,
    create_condition,
)
from tests.integration.encounter.support import (
    create_encounter,
    encounter_body,
)
from tests.integration.group.support import create_group, group_body
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

BASE = "/api/fhir/v1/document-references"
API = "/api/fhir/v1"

DOC_IDS = "https://fhir-server.dev/fhir/identifier-system/document-reference-id"
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"
LOINC = "http://loinc.org"
STATUS_SYSTEM = "http://hl7.org/fhir/document-reference-status"
RELATION_SYSTEM = "http://hl7.org/fhir/document-relationship-type"
CONFIDENTIALITY = "http://terminology.hl7.org/CodeSystem/v3-Confidentiality"
ACT_CODE = "http://terminology.hl7.org/CodeSystem/v3-ActCode"
SCT = "http://snomed.info/sct"
FORMAT = "urn:ihe:pcc:handp:2008"
FORMAT_SYSTEM = "http://ihe.net/fhir/ValueSet/IHE.FormatCode.codesystem"

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


def attachment(content_type: str = "application/pdf", **extra) -> dict:
    return {"contentType": content_type, **extra}


def content_entry(content_type: str = "application/pdf", **attachment_extra) -> dict:
    return {"attachment": attachment(content_type, **attachment_extra)}


def document_body(status: str = "current", **extra) -> dict:
    """A valid minimal document reference: R4 requires `status` and at least one `content` with
    an `attachment`."""
    return {
        "status": status,
        "content": [content_entry(url="https://documents.example.org/doc.pdf")],
        **extra,
    }


def full_body(
    organization_id: int,
    patient_id: int,
    practitioner_id: int,
    encounter_id: int,
    condition_id: int,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return document_body(
        resourceType="DocumentReference",
        masterIdentifier={"system": "urn:ietf:rfc:3986", "value": "urn:oid:1.2.3.4"},
        identifier=[
            {
                "system": DOC_IDS,
                "value": "DOC-1001",
                "type": {"coding": [{"system": V2_0203, "code": "ACSN"}]},
                "assigner": {"reference": f"Organization/{organization_id}"},
            }
        ],
        docStatus="final",
        type=concept(LOINC, "34133-9", "Summarization of episode note"),
        category=[concept(LOINC, "LP173421-1", "Report")],
        subject={"reference": f"Patient/{patient_id}"},
        date="2026-02-01T10:00:00Z",
        author=[{"reference": f"Practitioner/{practitioner_id}"}],
        authenticator={"reference": f"Practitioner/{practitioner_id}"},
        custodian={"reference": f"Organization/{organization_id}"},
        description="Discharge summary",
        securityLabel=[concept(CONFIDENTIALITY, "N", "normal")],
        content=[
            {
                "attachment": {
                    "contentType": "application/pdf",
                    "language": "en",
                    "url": "https://documents.example.org/doc-1001.pdf",
                    "size": 1234,
                    "title": "Discharge summary",
                    "creation": "2026-02-01",
                },
                "format": {"system": FORMAT_SYSTEM, "code": FORMAT},
            }
        ],
        context={
            "encounter": [{"reference": f"Encounter/{encounter_id}"}],
            "event": [concept(ACT_CODE, "AMB", "ambulatory")],
            "period": {"start": "2026-01-30", "end": "2026-02-01"},
            "facilityType": concept(SCT, "22232009", "Hospital"),
            "practiceSetting": concept(SCT, "408443003", "General medical practice"),
            "sourcePatientInfo": {"reference": f"Patient/{patient_id}"},
            "related": [{"reference": f"Condition/{condition_id}"}],
        },
    )


async def create_document(client, body: dict) -> int:
    """Create a document reference and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])
