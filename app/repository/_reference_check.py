"""The one write-time reference check shared by every content-based resource.

A FHIR document is a JSON tree; every `Reference` datatype in it is an object with a `reference`
string. On create and patch, every such string that is a *relative* `Type/<id>` naming a resource
this server has must resolve to a row in the caller's org - otherwise the write is rejected with
422. Nothing else is checked here:

  - an absolute URL, a `#contained` reference, a Reference with only `identifier` / `type` /
    `display`, and a relative reference to a type this server does not have are stored as sent
    (they may point at another system);
  - whether the target *type* fits the element (`Observation/1` in `CarePlan.subject`) is the
    FHIR validator's job (the `java_validator` backend reads the real R4 definitions; the native
    JSON-schema check does not).

Which types "this server has" is read from `RESOURCE_REGISTRY` (app.core.reference_resolver):
the registered types whose model is content-based (has a `content` column) - the rebuilt
resources. The registry also still lists resources that have not been rebuilt (old normalized
models whose routes are switched off, so nothing can create them); they are not checked until they
are rebuilt. Registering a rebuilt resource is therefore all it takes for every other resource to
start checking references to it - no per-resource list to update.

The document is walked generically, so every Reference is found wherever it sits: a nested
backbone element, `identifier.assigner`, a note's `authorReference`, an extension's
`valueReference`, a contained resource.
"""

from __future__ import annotations

import re

from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists

# `Type/<id>`, optionally version-specific (`Type/<id>/_history/<vid>`). A relative reference's id
# is this server's numeric public id; anything else (an absolute URL, `#contained`, a logical id
# that is not numeric) matches nothing and is left alone.
_RELATIVE = re.compile(
    r"^(?P<type>[A-Z][A-Za-z]+)/(?P<id>\d+)(?:/_history/[A-Za-z0-9\-.]{1,64})?$"
)


def checkable_types() -> frozenset[str]:
    """The resource types a relative reference is checked against: registered and content-based."""
    return frozenset(
        resource_type
        for resource_type, (model, _id_column) in RESOURCE_REGISTRY.items()
        if hasattr(model, "content")
    )


def find_local_references(
    document: dict, types: frozenset[str] | None = None
) -> list[tuple[str, str, int]]:
    """Every relative reference in `document` to a checkable type, as
    (element path, resource type, public id) - e.g.
    ("activity[1].detail.performer[0]", "CareTeam", 390001). The path is for the error message."""
    types = checkable_types() if types is None else types
    found: list[tuple[str, str, int]] = []

    def walk(node, path: str) -> None:
        if isinstance(node, dict):
            reference = node.get("reference")
            if isinstance(reference, str):
                match = _RELATIVE.match(reference)
                if match and match["type"] in types:
                    found.append((path or "reference", match["type"], int(match["id"])))
            for key, value in node.items():
                if key == "reference" and isinstance(value, str):
                    continue
                walk(value, f"{path}.{key}" if path else key)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(document, "")
    return found


async def validate_local_references(session, tenant_id: str, document: dict) -> None:
    """Raise a 422 (BusinessRuleViolationError) for the first relative reference in `document`
    that does not resolve in `tenant_id`. Each distinct target is looked up once."""
    seen: set[tuple[str, int]] = set()
    for path, resource_type, resource_id in find_local_references(document):
        if (resource_type, resource_id) in seen:
            continue
        seen.add((resource_type, resource_id))
        await ensure_resource_exists(
            session, resource_type, resource_id, org_id=tenant_id, field_name=path
        )
