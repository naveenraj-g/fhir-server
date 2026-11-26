"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.questionnaire_response import (
    QuestionnaireResponse,
    QuestionnaireResponsePatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "QuestionnaireResponse",
    "identifier": {
        "system": "https://fhir-server.dev/fhir/identifier-system/questionnaire-response-id",
        "value": "QR-1001",
    },
    "questionnaire": "https://fhir-server.dev/fhir/Questionnaire/phq-9",
    "status": "completed",
    "subject": {"type": "Patient", "display": "Example patient"},
    "encounter": {"type": "Encounter", "display": "Example encounter"},
    "authored": "2026-02-01T10:00:00Z",
    "author": {"type": "Practitioner", "display": "Example practitioner"},
    "source": {"type": "Patient", "display": "Example patient"},
    "item": [
        {
            "linkId": "1",
            "text": "Mood",
            "item": [
                {
                    "linkId": "1.1",
                    "text": "Little interest or pleasure in doing things",
                    "answer": [{"valueInteger": 2}],
                }
            ],
        }
    ],
}

_PATCH_EXAMPLE = {
    "status": "amended",
    "item": [{"linkId": "1", "answer": [{"valueString": "corrected"}]}],
}


class QuestionnaireResponseCreateSchema(QuestionnaireResponse):
    "POST body - a FHIR R4 QuestionnaireResponse resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class QuestionnaireResponsePatchSchema(QuestionnaireResponsePatch):
    "PATCH body - a partial FHIR R4 QuestionnaireResponse (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})
