"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.communication_request import (
    CommunicationRequest,
    CommunicationRequestPatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "CommunicationRequest",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/communication-request-id",
            "value": "CR-1",
        }
    ],
    "basedOn": [{"reference": "CarePlan/290001"}],
    "groupIdentifier": {"system": "urn:groups", "value": "G-1"},
    "status": "active",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/communication-category",
                    "code": "reminder",
                }
            ]
        }
    ],
    "priority": "routine",
    "medium": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationMode",
                    "code": "WRITTEN",
                }
            ]
        }
    ],
    "subject": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "payload": [{"contentString": "Please book your follow-up visit."}],
    "occurrenceDateTime": "2026-02-01T09:00:00Z",
    "authoredOn": "2026-01-15T09:00:00Z",
    "requester": {"reference": "Practitioner/30001"},
    "recipient": [{"reference": "Patient/10001"}],
    "sender": {"reference": "Practitioner/30001"},
}

_PATCH_EXAMPLE = {"status": "completed", "occurrenceDateTime": "2026-02-02T09:00:00Z"}


class CommunicationRequestCreateSchema(CommunicationRequest):
    "POST body - a FHIR R4 CommunicationRequest resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class CommunicationRequestPatchSchema(CommunicationRequestPatch):
    "PATCH body - a partial FHIR R4 CommunicationRequest (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})
