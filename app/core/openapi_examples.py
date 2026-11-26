"""Request and response examples for the routes that are not FHIR resource CRUD.

Terminology, FHIR profiles, `/validate` and the health probes take or return bodies whose
OpenAPI schema is generic (`object`, `Parameters`) or has no example of its own, so Swagger UI
would show placeholders. The resource routes get their examples from their generated schemas;
these are written by hand, from real responses, and attached by operation id in `app.main`'s
OpenAPI hook. The sample data is self-consistent: SNOMED CT 38341003 / 59621000, ICD-10-CM I10.
"""

from __future__ import annotations

from app.schemas.fhir_profile import FhirProfileCreateSchema
from app.schemas.organization.input.core import _CREATE_EXAMPLE as _ORGANIZATION

_ICD = "http://hl7.org/fhir/sid/icd-10-cm"
_SCT = "http://snomed.info/sct"
_VS = "https://fhir-server.dev/fhir/ValueSet/hypertension-codes"
_LOCAL = "https://fhir-server.dev/fhir/CodeSystem/local-findings"
_NOW = "2026-01-15T09:30:00Z"
_DISPLAY = "Essential (primary) hypertension"


def _parameters(*entries: dict) -> dict:
    return {"resourceType": "Parameters", "parameter": list(entries)}


def _p(name: str, kind: str, value) -> dict:
    return {"name": name, kind: value}


def _page(items: list, limit: int = 50) -> dict:
    return {"total": len(items), "limit": limit, "offset": 0, "data": items}


# ── Terminology data ──────────────────────────────────────────────────────────

_ICD_CONCEPT = {
    "id": 1,
    "code": "I10",
    "display": _DISPLAY,
    "definition": None,
    "active": True,
    "system": _ICD,
    "system_name": "ICD10CM",
}
_SCT_CONCEPT = {
    "id": 2,
    "code": "38341003",
    "display": "Hypertensive disorder",
    "definition": None,
    "active": True,
    "system": _SCT,
    "system_name": "SNOMEDCT",
}
_CODE_SYSTEM = {
    "id": 1,
    "canonical_url": _ICD,
    "name": "ICD10CM",
    "title": "ICD-10-CM",
    "version": "2026",
    "publisher": "CMS",
    "content_mode": "complete",
    "active": True,
}
_VALUE_SET = {
    "id": 1,
    "canonical_url": _VS,
    "name": "HypertensionCodes",
    "title": "Hypertension codes",
    "description": "Codes used to record hypertension.",
    "version": "1.0",
    "binding_strength": "extensible",
    "active": True,
}
_ORG_CONCEPT = {
    "id": 4,
    "code": "CUSTOM-01",
    "display": "Custom Finding",
    "definition": "Custom clinical finding description",
    "active": True,
    "system": _LOCAL,
    "system_name": "LocalFindings",
    "user_id": "user_abc123",
    "org_id": "org_abc123",
    "created_at": _NOW,
}
_LOOKUP = {"found": True, "concept": _ICD_CONCEPT, "code_system": _CODE_SYSTEM}

_LOOKUP_OUT = _parameters(
    _p("name", "valueString", "ICD10CM"),
    _p("version", "valueString", "2026"),
    _p("display", "valueString", _DISPLAY),
)
_CS_VALIDATE_OUT = _parameters(
    _p("result", "valueBoolean", True),
    _p("message", "valueString", f"Code 'I10' is valid in CodeSystem '{_ICD}'."),
    _p("display", "valueString", _DISPLAY),
)
_SUBSUMES_OUT = _parameters(_p("outcome", "valueCode", "subsumes"))
_EXPANSION = {
    "resourceType": "ValueSet",
    "url": _VS,
    "version": "1.0",
    "name": "HypertensionCodes",
    "title": "Hypertension codes",
    "status": "active",
    "expansion": {
        "timestamp": _NOW,
        "total": 1,
        "contains": [{"system": _ICD, "code": "I10", "display": _DISPLAY}],
    },
}
_VS_VALIDATE_OUT = {
    "result": True,
    "message": f"Code 'I10' is a member of ValueSet '{_VS}'.",
    "display": _DISPLAY,
}
_TRANSLATE_OUT = _parameters(
    _p("result", "valueBoolean", True),
    {
        "name": "match",
        "part": [
            _p("equivalence", "valueCode", "equivalent"),
            _p(
                "concept",
                "valueCoding",
                {"system": _ICD, "code": "I10", "display": _DISPLAY},
            ),
        ],
    },
)

# ── FHIR profile data ─────────────────────────────────────────────────────────

_PROFILE_REQUEST = FhirProfileCreateSchema.model_config["json_schema_extra"]["example"]
_PROFILE_URL = (
    "https://fhir-server.dev/fhir/StructureDefinition/org-org_abc123-organization"
)
_PROFILE = {
    "id": 149,
    "resource_type": "Organization",
    "scope_level": "organization",
    "scope_id": "org_abc123",
    "parent_profile_id": 101,
    "canonical_url": _PROFILE_URL,
    "version": "1",
    "status": "draft",
    "structure_definition": {
        **_PROFILE_REQUEST["structure_definition"],
        "id": "628d2100-966d-4fb8-8d47-633cab5e98d2",
        "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Organization",
        "derivation": "constraint",
        "url": _PROFILE_URL,
    },
    "created_by": "user_abc123",
    "updated_by": "user_abc123",
    "created_at": _NOW,
    "updated_at": None,
}

# ── Request bodies, by operation id ───────────────────────────────────────────

_LOOKUP_IN = _parameters(_p("system", "valueUri", _ICD), _p("code", "valueCode", "I10"))

REQUEST_EXAMPLES: dict[str, dict] = {
    "lookup_terminology_concept": {"system": _ICD, "code": "I10"},
    "lookup_terminology_concepts_batch": {
        "items": [
            {"system": _ICD, "code": "I10"},
            {"system": _SCT, "code": "38341003"},
        ]
    },
    "validate_terminology_code": {
        "resource": "Condition",
        "field": "code",
        "system": _ICD,
        "code": "I10",
    },
    "translate_terminology_concept": {
        "system": _SCT,
        "code": "38341003",
        "target_system": _ICD,
    },
    "codesystem_lookup_post": _LOOKUP_IN,
    "codesystem_validate_code_post": _parameters(
        _p("url", "valueUri", _ICD), _p("code", "valueCode", "I10")
    ),
    "codesystem_subsumes_post": _parameters(
        _p("system", "valueUri", _SCT),
        _p("codeA", "valueCode", "38341003"),
        _p("codeB", "valueCode", "59621000"),
    ),
    "codesystem_find_matches_post": _parameters(
        _p("system", "valueUri", _SCT),
        _p("exact", "valueBoolean", True),
        {
            "name": "property",
            "part": [
                _p("code", "valueCode", "parent"),
                _p("value", "valueString", "38341003"),
            ],
        },
    ),
    "valueset_expand_operation_type_post": _parameters(
        _p("url", "valueUri", _VS), _p("count", "valueInteger", 10)
    ),
    "valueset_validate_code_operation_type_post": _parameters(
        _p("url", "valueUri", _VS),
        _p("coding", "valueCoding", {"system": _ICD, "code": "I10"}),
    ),
    "conceptmap_translate_post": _parameters(
        _p("system", "valueUri", _SCT),
        _p("code", "valueCode", "38341003"),
        _p("targetsystem", "valueUri", _ICD),
    ),
    "closure_operation": _parameters(
        _p("name", "valueString", "problem-list"),
        _p("concept", "valueCoding", {"system": _SCT, "code": "59621000"}),
    ),
    "validate_fhir_resource": _ORGANIZATION,
}

# ── Success responses, by operation id ────────────────────────────────────────

RESPONSE_EXAMPLES: dict[str, dict] = {
    "health_check": {"status": "ok", "req_id": "3f2b8c1e-6a4d-4f0a-9c57-2d1e8b6a4f10"},
    "readiness_check": {
        "status": "ok",
        "req_id": "3f2b8c1e-6a4d-4f0a-9c57-2d1e8b6a4f10",
        "checks": {"database": "ok", "redis": "ok"},
    },
    "create_fhir_profile": _PROFILE,
    "list_fhir_profiles": _page([_PROFILE]),
    "get_fhir_profile": _PROFILE,
    "patch_fhir_profile": {**_PROFILE, "updated_at": _NOW},
    "activate_fhir_profile": {**_PROFILE, "status": "active", "updated_at": _NOW},
    "validate_fhir_resource": {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "information",
                "code": "informational",
                "diagnostics": "No issues detected. Resource is valid against the most specific applicable profile.",
            }
        ],
    },
    "list_terminology_code_systems": {"total": 1, "data": [_CODE_SYSTEM]},
    "list_terminology_value_sets": _page([_VALUE_SET]),
    "expand_terminology_value_set": {
        "value_set": _VALUE_SET,
        "total": 1,
        "limit": 50,
        "offset": 0,
        "concepts": [_ICD_CONCEPT],
    },
    "search_terminology_concepts": _page([_ICD_CONCEPT], limit=20),
    "lookup_terminology_concept": _LOOKUP,
    "lookup_terminology_concepts_batch": {
        "results": [_LOOKUP, {"found": False, "concept": None, "code_system": None}]
    },
    "get_terminology_concepts_for_field": {
        "resource": "Condition",
        "field": "code",
        "value_set": _VALUE_SET,
        "binding_strength": "extensible",
        "multiple_allowed": False,
        "total": 1,
        "limit": 50,
        "offset": 0,
        "concepts": [_ICD_CONCEPT],
    },
    "validate_terminology_code": {
        "valid": True,
        "in_value_set": True,
        "binding_strength": "extensible",
        "concept": _ICD_CONCEPT,
        "value_set": _VALUE_SET,
        "message": "Code 'I10' is valid for Condition.code.",
    },
    "translate_terminology_concept": {
        "source_concept": _SCT_CONCEPT,
        "source_system": _SCT,
        "source_code": "38341003",
        "target_system": _ICD,
        "translations": [
            {"concept": _ICD_CONCEPT, "equivalence": "equivalent", "confidence": 1.0}
        ],
        "found": True,
    },
    "list_concept_maps": _page(
        [
            {
                "id": 1,
                "source_concept": _SCT_CONCEPT,
                "target_concept": _ICD_CONCEPT,
                "equivalence": "equivalent",
                "confidence": 1.0,
            }
        ]
    ),
    "add_concept_map": {
        "inserted": True,
        "source": _SCT_CONCEPT,
        "target": _ICD_CONCEPT,
        "equivalence": "equivalent",
        "confidence": 1.0,
    },
    "list_org_concepts": _page([_ORG_CONCEPT]),
    "create_org_concept": _ORG_CONCEPT,
    "get_org_concept": _ORG_CONCEPT,
    "patch_org_concept": {
        **_ORG_CONCEPT,
        "display": "Updated Finding Display",
        "definition": "Updated clinical finding definition",
    },
    "codesystem_lookup_get": _LOOKUP_OUT,
    "codesystem_lookup_post": _LOOKUP_OUT,
    "codesystem_validate_code_get": _CS_VALIDATE_OUT,
    "codesystem_validate_code_post": _CS_VALIDATE_OUT,
    "codesystem_subsumes_get": _SUBSUMES_OUT,
    "codesystem_subsumes_post": _SUBSUMES_OUT,
    "codesystem_find_matches_post": _parameters(
        _p(
            "comment",
            "valueString",
            "No property-based concept matching is implemented — this repository has no CodeSystem.property data to match against.",
        )
    ),
    "valueset_expand_operation_type": _EXPANSION,
    "valueset_expand_operation_type_post": _EXPANSION,
    "valueset_expand_operation_instance": _EXPANSION,
    "valueset_validate_code_operation_type": _VS_VALIDATE_OUT,
    "valueset_validate_code_operation_type_post": _VS_VALIDATE_OUT,
    "valueset_validate_code_operation_instance": _VS_VALIDATE_OUT,
    "conceptmap_translate_get": _TRANSLATE_OUT,
    "conceptmap_translate_post": _TRANSLATE_OUT,
    "closure_operation": {
        "resourceType": "ConceptMap",
        "id": "problem-list",
        "version": "2",
        "status": "active",
        "experimental": False,
        "date": _NOW,
        "group": [
            {
                "source": _SCT,
                "target": _SCT,
                "element": [
                    {
                        "code": "59621000",
                        "target": [{"code": "38341003", "equivalence": "subsumes"}],
                    }
                ],
            }
        ],
    },
    "get_terminology_capabilities": {
        "resourceType": "TerminologyCapabilities",
        "status": "active",
        "date": _NOW,
        "kind": "instance",
        "implementation": {
            "description": "Embedded FHIR R4 terminology service — CodeSystem/ValueSet/ConceptMap operations over this repository's own loaded terminologies."
        },
        "codeSystem": [
            {
                "uri": _SCT,
                "version": [{"code": "2026-01", "isDefault": True}],
                "subsumption": True,
            }
        ],
        "expansion": {
            "hierarchical": False,
            "paging": True,
            "incomplete": False,
            "parameter": [
                {"name": "url", "documentation": "Canonical ValueSet URL"},
                {"name": "count", "documentation": "Page size"},
            ],
        },
        "codeSearch": "explicit",
        "validateCode": {"translations": False},
        "translation": {"needsMap": True},
        "closure": {"translation": False},
    },
}


def add_examples(schema: dict) -> None:
    """Attach the examples above to their operations' request and 2xx response bodies."""
    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            op_id = operation.get("operationId")
            if op_id in REQUEST_EXAMPLES and "requestBody" in operation:
                for media in operation["requestBody"]["content"].values():
                    media["example"] = REQUEST_EXAMPLES[op_id]
            if op_id not in RESPONSE_EXAMPLES:
                continue
            for status, response in operation.get("responses", {}).items():
                if status.startswith("2"):
                    for media in response.get("content", {}).values():
                        media["example"] = RESPONSE_EXAMPLES[op_id]
                        if not media.get("schema"):
                            media["schema"] = {"type": "object"}
