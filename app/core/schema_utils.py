from typing import Any

# Shared sub-schemas (Pydantic `$defs`) collected from every response schema built with
# `inline_schema()`. app.main's custom OpenAPI hook publishes them under `components.schemas`, once
# each, so a fully-typed FHIR resource (hundreds of nested definitions) is described once instead of
# being copied into every route that mentions it.
COMPONENT_SCHEMAS: dict[str, dict] = {}

_DEFS_PREFIX = "#/$defs/"
_COMPONENTS_PREFIX = "#/components/schemas/"


def _rewrite(node: Any) -> Any:
    """Point every `#/$defs/X` reference at `#/components/schemas/X`."""
    if isinstance(node, dict):
        out = {}
        for key, value in node.items():
            if (
                key == "$ref"
                and isinstance(value, str)
                and value.startswith(_DEFS_PREFIX)
            ):
                out[key] = _COMPONENTS_PREFIX + value[len(_DEFS_PREFIX) :]
            elif key != "$defs":
                out[key] = _rewrite(value)
        return out
    if isinstance(node, list):
        return [_rewrite(item) for item in node]
    return node


def inline_schema(schema: dict) -> dict:
    """
    Make a Pydantic `model_json_schema()` output safe to embed in a FastAPI `responses={}` dict.

    Pydantic puts sub-model schemas under a top-level `$defs` and refers to them with
    `"$ref": "#/$defs/<Name>"`. Once the schema is embedded in an OpenAPI document that path no
    longer resolves, because `$defs` is not at the document root. The definitions are therefore
    moved into COMPONENT_SCHEMAS (published as `components.schemas` by the app's OpenAPI hook) and
    the references are rewritten to `#/components/schemas/<Name>`.

    Earlier versions copied each definition into every place that used it. That is fine for a small
    model but explodes for fully-typed FHIR resources (a Task inlines to megabytes, because
    Extension, CodeableConcept, Reference, ... recur at every level), and it could not describe a
    recursive element (Questionnaire.item.item) at all.
    """
    for name, definition in schema.get("$defs", {}).items():
        rewritten = _rewrite(definition)
        existing = COMPONENT_SCHEMAS.get(name)
        if existing is not None and existing != rewritten:
            raise ValueError(
                f"Two different schemas are both named {name!r}; rename one of the Pydantic "
                "classes so OpenAPI can publish both."
            )
        COMPONENT_SCHEMAS[name] = rewritten
    return _rewrite(schema)
