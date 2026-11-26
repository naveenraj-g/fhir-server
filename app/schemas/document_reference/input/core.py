"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.document_reference import (
    DocumentReference,
    DocumentReferencePatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "DocumentReference",
    "masterIdentifier": {
        "system": "urn:ietf:rfc:3986",
        "value": "urn:oid:1.2.840.113556.1.8000.2554.58783.21864",
    },
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/document-reference-id",
            "value": "DOC-1001",
        }
    ],
    "status": "current",
    "docStatus": "final",
    "type": {
        "coding": [
            {
                "system": "http://loinc.org",
                "code": "34133-9",
                "display": "Summarization of episode note",
            }
        ]
    },
    "category": [
        {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "LP173421-1",
                    "display": "Report",
                }
            ]
        }
    ],
    "subject": {"type": "Patient", "display": "Example patient"},
    "date": "2026-02-01T10:00:00Z",
    "author": [{"type": "Practitioner", "display": "Example practitioner"}],
    "custodian": {"type": "Organization", "display": "Example organization"},
    "description": "Discharge summary",
    "content": [
        {
            "attachment": {
                "language": "en",
                "url": "https://fhir-server.dev/documents/doc-1001.pdf",
                "title": "Discharge summary",
            },
            "format": {
                "system": "http://ihe.net/fhir/ValueSet/IHE.FormatCode.codesystem",
                "code": "urn:ihe:pcc:handp:2008",
            },
        }
    ],
    "context": {
        "encounter": [{"type": "Encounter", "display": "Example encounter"}],
        "period": {"start": "2026-01-30", "end": "2026-02-01"},
    },
}

_PATCH_EXAMPLE = {"status": "superseded", "description": "Superseded discharge summary"}


class DocumentReferenceCreateSchema(DocumentReference):
    "POST body - a FHIR R4 DocumentReference resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class DocumentReferencePatchSchema(DocumentReferencePatch):
    "PATCH body - a partial FHIR R4 DocumentReference (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})
