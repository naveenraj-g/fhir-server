"""Generic FHIR R4 `Parameters` resource helpers — shared by every
`$`-operation route this server implements (terminology's
`$lookup`/`$validate-code`/`$expand`/`$subsumes`/`$translate`/`$closure`
today; a future non-terminology operation, e.g. ActivityDefinition's
`$apply`, reuses these same functions rather than reinventing Parameters
handling per operation).

See https://www.hl7.org/fhir/R4/parameters.html — `Parameters` is itself a
resource: `{resourceType: "Parameters", parameter: [{name, valueX,
resource, part: [...]}]}`. Every operation's POST body, and every
operation's JSON response except `$expand` (returns a `ValueSet` directly)
and `$closure` (returns a `ConceptMap` directly), is one of these — see
each route's own code for the two exceptions.

Deliberately NOT a Pydantic model: `Parameters.parameter[].value[x]` is a
true choice type across ~50 FHIR primitive/complex types, and every
operation here only ever touches a handful of them, so a plain dict
(built/read via the functions below) is less code than either a giant
union-typed model or 8 near-identical per-operation ones."""

from typing import Any


def build_parameters(*entries: dict[str, Any] | None) -> dict:
    """Wraps non-None parameter entries into a `Parameters` resource body.
    Build each entry with one of the `param_*()` helpers below, or by hand
    for a Coding/complex value — `None` entries are dropped, so a caller
    can write `build_parameters(param_string("version", cs.version), ...)`
    even when `version` is `None`, instead of filtering a list by hand at
    every call site."""
    return {
        "resourceType": "Parameters",
        "parameter": [e for e in entries if e is not None],
    }


def param(name: str, **value_fields: Any) -> dict:
    """One `Parameters.parameter` entry: `{"name": name, **value_fields}`."""
    return {"name": name, **value_fields}


def param_string(name: str, value: str | None) -> dict | None:
    return None if value is None else param(name, valueString=value)


def param_boolean(name: str, value: bool | None) -> dict | None:
    return None if value is None else param(name, valueBoolean=value)


def param_code(name: str, value: str | None) -> dict | None:
    return None if value is None else param(name, valueCode=value)


def param_integer(name: str, value: int | None) -> dict | None:
    return None if value is None else param(name, valueInteger=value)


def param_coding(name: str, value: dict | None) -> dict | None:
    """`value` is a plain Coding dict (system/version/code/display/
    userSelected) — already the shape `FHIRCoding.model_dump(exclude_none=True)`
    produces (app/schemas/datatypes/coding.py)."""
    return None if value is None else param(name, valueCoding=value)


def param_part(name: str, *parts: dict | None) -> dict:
    """A composite parameter (e.g. `$lookup`'s `designation`, `$translate`'s
    `match`) — one entry whose own `part[]` holds nested parameter entries.
    Unlike `build_parameters()`'s top-level entries, this one is NOT
    optional-by-default: a composite parameter's own presence is always the
    caller's explicit choice. Filter `parts` yourself before calling if some
    of its children are conditionally absent."""
    return {"name": name, "part": [p for p in parts if p is not None]}


def get_param(body: dict, name: str) -> Any | None:
    """Reads the first occurrence of a simple `value[x]` parameter named
    `name` from a POST `Parameters` body — returns whichever `valueX` value
    is present (`valueString`, `valueUri`, `valueCode`, `valueBoolean`,
    `valueInteger`, `valueCoding`, `valueCodeableConcept`, ...), not just
    one specific type, since the caller already knows which shape it asked
    for. Returns `None` if absent. Does not resolve `resource`-valued
    parameters (inline `ValueSet`/`CodeSystem` bodies) — see
    `get_param_resource()`."""
    for p in body.get("parameter", []):
        if p.get("name") == name:
            for key, val in p.items():
                if key.startswith("value"):
                    return val
    return None


def get_param_resource(body: dict, name: str) -> dict | None:
    """Reads an inline-resource-valued parameter (e.g. `$expand`'s
    `valueSet`, `$validate-code`'s `codeSystem`) — these carry `resource`,
    not a `valueX` field."""
    for p in body.get("parameter", []):
        if p.get("name") == name:
            return p.get("resource")
    return None


def get_params_list(body: dict, name: str) -> list[dict]:
    """Every occurrence of a repeatable parameter named `name` (e.g.
    `$lookup`'s `property`, `$closure`'s `concept`) — returns each full
    parameter dict (not just its value), since some repeatable parameters
    are composite (`part[]`) rather than a single `valueX`."""
    return [p for p in body.get("parameter", []) if p.get("name") == name]
