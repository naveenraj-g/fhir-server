"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.questionnaire import Questionnaire, QuestionnairePatch

_CREATE_EXAMPLE = {
    "resourceType": "Questionnaire",
    "url": "https://fhir-server.dev/fhir/Questionnaire/phq-9",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/questionnaire-id",
            "value": "PHQ-9",
        }
    ],
    "version": "1.0",
    "name": "PHQ9",
    "title": "Patient Health Questionnaire 9",
    "status": "active",
    "subjectType": ["Patient"],
    "date": "2026-01-15",
    "publisher": "Example Health",
    "description": "A nine-question depression screen.",
    "useContext": [
        {
            "code": {
                "system": "http://terminology.hl7.org/CodeSystem/usage-context-type",
                "code": "focus",
            },
            "valueCodeableConcept": {
                "coding": [{"system": "http://snomed.info/sct", "code": "35489007"}]
            },
        }
    ],
    "jurisdiction": [{"coding": [{"system": "urn:iso:std:iso:3166", "code": "US"}]}],
    "effectivePeriod": {"start": "2026-01-01"},
    "code": [{"system": "http://loinc.org", "code": "44249-1"}],
    "item": [
        {
            "linkId": "1",
            "text": "Mood",
            "type": "group",
            "item": [
                {
                    "linkId": "1.1",
                    "definition": "http://example.org/definitions/interest",
                    "code": [{"system": "http://loinc.org", "code": "44250-9"}],
                    "text": "Little interest or pleasure in doing things",
                    "type": "choice",
                    "required": True,
                    "answerOption": [
                        {
                            "valueCoding": {
                                "system": "http://loinc.org",
                                "code": "LA6568-5",
                            }
                        }
                    ],
                }
            ],
        }
    ],
}

_PATCH_EXAMPLE = {
    "status": "retired",
    "title": "Patient Health Questionnaire 9 (retired)",
}


class QuestionnaireCreateSchema(Questionnaire):
    "POST body - a FHIR R4 Questionnaire resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class QuestionnairePatchSchema(QuestionnairePatch):
    "PATCH body - a partial FHIR R4 Questionnaire (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})
