"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.plan_definition import (
    PlanDefinition,
    PlanDefinitionPatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "PlanDefinition",
    "url": "https://fhir-server.dev/fhir/PlanDefinition/discharge-pathway",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/plan-definition-id",
            "value": "AD-1",
        }
    ],
    "version": "1.0",
    "name": "FollowUpVisit",
    "title": "Follow-up visit",
    "status": "active",
    "date": "2026-01-15",
    "publisher": "Example Health",
    "description": "Book a follow-up visit.",
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
    "topic": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/definition-topic",
                    "code": "treatment",
                }
            ]
        }
    ],
    "type": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/plan-definition-type",
                "code": "order-set",
            }
        ]
    },
    "action": [
        {
            "title": "Book a visit",
            "definitionCanonical": "http://example.org/fhir/ActivityDefinition/follow-up-visit",
        }
    ],
}

_PATCH_EXAMPLE = {"status": "retired", "version": "1.1"}


class PlanDefinitionCreateSchema(PlanDefinition):
    "POST body - a FHIR R4 PlanDefinition resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class PlanDefinitionPatchSchema(PlanDefinitionPatch):
    "PATCH body - a partial FHIR R4 PlanDefinition (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})
