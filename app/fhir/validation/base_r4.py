"""Base-layer FHIR R4 structural validation.

Uses HL7's published `fhir.schema.json` (app/fhir/spec/, see its README) as
an independent oracle — the first link in the base -> country -> resource
profile chain described in
docs/architecture/fhir-profiling-and-extensibility-strategy.md. This layer
only catches what a JSON Schema can express: required elements, cardinality
(0..1 vs 0..*), primitive formats, and required-binding enums. It does NOT
catch invariants (cross-field/cross-resource rules like Organization's
org-1 "name or identifier required") — those are a separate, not-yet-built
layer, since not every resource has any.
"""

import json
from pathlib import Path

from jsonschema import Draft6Validator

from app.errors.fhir_codes import IssueType

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "spec" / "fhir.schema.json"
_FHIR_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
_DEFINITIONS = _FHIR_SCHEMA["definitions"]

# jsonschema's own `ValidationError.validator` keyword -> the nearest real
# HL7 IssueType. Not exhaustive (jsonschema has more keywords than FHIR has
# matching issue types) — unmapped keywords fall back to IssueType.INVALID
# (the parent code) in validate_base_r4() below, which is always a legal
# choice, just less specific.
_JSONSCHEMA_KEYWORD_TO_ISSUE_TYPE = {
    "required": IssueType.REQUIRED,
    "type": IssueType.VALUE,
    "pattern": IssueType.VALUE,
    "format": IssueType.VALUE,
    "minLength": IssueType.VALUE,
    "maxLength": IssueType.VALUE,
    "enum": IssueType.CODE_INVALID,
    "const": IssueType.VALUE,
    "additionalProperties": IssueType.STRUCTURE,
}

_validators: dict[str, Draft6Validator] = {}


def _validator_for(resource_type: str) -> Draft6Validator:
    """One Draft6Validator per resource type, built once and cached. Each
    wraps just that resource's own definition, plus the full shared
    `definitions` dict alongside it so every internal `#/definitions/...`
    $ref used by the resource (Identifier, CodeableConcept, Address, ...)
    still resolves within the same schema document."""
    validator = _validators.get(resource_type)
    if validator is None:
        if resource_type not in _DEFINITIONS:
            raise ValueError(
                f"No base R4 definition for resource type {resource_type!r}"
            )
        schema = {
            "$schema": _FHIR_SCHEMA["$schema"],
            "definitions": _DEFINITIONS,
            "$ref": f"#/definitions/{resource_type}",
        }
        validator = Draft6Validator(schema)
        _validators[resource_type] = validator
    return validator


def validate_base_r4(resource_type: str, fhir_resource: dict) -> list[dict]:
    """Validates `fhir_resource` (a true FHIR JSON dict — e.g. a payload
    mapper's output, not the DB-shaped input schema) against HL7's base R4
    JSON Schema for `resource_type`. Returns a list of
    `{"field": str, "message": str, "issue_type": IssueType}` dicts, sorted
    by path, empty when valid — `issue_type` is a best-effort mapping from
    jsonschema's own failure keyword (see _JSONSCHEMA_KEYWORD_TO_ISSUE_TYPE
    above), falling back to the generic IssueType.INVALID when a keyword
    has no closer match."""
    validator = _validator_for(resource_type)
    errors = [
        {
            "field": ".".join(str(p) for p in err.absolute_path) or "(root)",
            "message": err.message,
            "issue_type": _JSONSCHEMA_KEYWORD_TO_ISSUE_TYPE.get(
                err.validator, IssueType.INVALID
            ),
        }
        for err in sorted(
            validator.iter_errors(fhir_resource), key=lambda e: list(e.absolute_path)
        )
    ]
    return errors


def inline_schema_for_docs(resource_type: str) -> dict:
    """Returns `resource_type`'s own real HL7 JSON Schema definition with
    every internal `$ref` to a shared datatype (Identifier, CodeableConcept,
    ElementDefinition, ...) recursively inlined — same flattening
    app/core/schema_utils.py's inline_schema() does for Pydantic-generated
    schemas, adapted to this module's own "definitions"/"#/definitions/..."
    convention (HL7's own, not Pydantic's "$defs"/"#/$defs/...").

    For embedding a real FHIR resource's complete shape directly into
    OpenAPI docs (see app/routers/fhir_profile/) without hand-building a
    Pydantic model for it — e.g. StructureDefinition, which would otherwise
    need ~50+ fields modeled by hand just to document one request body.
    Reuses the exact same `_DEFINITIONS` dict validate_base_r4() already
    has loaded, so the documented shape and the enforced shape can never
    drift apart — they're the same source.

    Memoizes each named definition's fully-resolved form exactly once
    (`resolved`, keyed by name) — FHIR's datatypes cross-reference each
    other heavily (Extension alone touches most of the datatype catalog
    through its value[x] choices), so without memoization this blows up
    combinatorially: every distinct reference path re-expands the same
    definitions from scratch, and the same shared datatypes get re-visited
    many times over. `seen` (unlike `resolved`) tracks only the names
    currently *mid-resolution* on the active path, purely to break real
    cycles (e.g. Extension nesting itself) with a placeholder — it is not
    a cache."""
    if resource_type not in _DEFINITIONS:
        raise ValueError(f"No base R4 definition for resource type {resource_type!r}")

    resolved: dict[str, object] = {}

    def _resolve(node, seen: frozenset):
        if isinstance(node, dict):
            if "$ref" in node and node["$ref"].startswith("#/definitions/"):
                name = node["$ref"][len("#/definitions/"):]
                if name in seen:
                    return {"type": "object", "description": f"(recursive ref: {name})"}
                if name in resolved:
                    return resolved[name]
                if name not in _DEFINITIONS:
                    return {"type": "object", "description": f"(unresolved ref: {name})"}
                result = _resolve(_DEFINITIONS[name], seen | {name})
                resolved[name] = result
                return result
            return {k: _resolve(v, seen) for k, v in node.items()}
        if isinstance(node, list):
            return [_resolve(item, seen) for item in node]
        return node

    return _resolve(_DEFINITIONS[resource_type], frozenset({resource_type}))
