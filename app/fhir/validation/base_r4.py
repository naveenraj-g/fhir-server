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

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "spec" / "fhir.schema.json"
_FHIR_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
_DEFINITIONS = _FHIR_SCHEMA["definitions"]

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
    `{"field": str, "message": str}` dicts, sorted by path, empty when
    valid."""
    validator = _validator_for(resource_type)
    errors = [
        {"field": ".".join(str(p) for p in err.absolute_path) or "(root)", "message": err.message}
        for err in sorted(
            validator.iter_errors(fhir_resource), key=lambda e: list(e.absolute_path)
        )
    ]
    return errors
