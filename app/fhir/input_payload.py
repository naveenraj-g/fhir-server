"""
Pre-write validation documents for resources whose create/patch body is
already FHIR-shaped (built on app.schemas.fhir_input — Organization first).

For those resources there is nothing to *map*: the request body is already
the FHIR resource, so the per-resource `payload.py` mapper that the
flattened-input resources need disappears.

What gets validated is the **raw request body** (the parsed JSON, before
Pydantic), not the Pydantic model — so base R4 validation sees everything
the client actually sent: every valid element passes (and, for a resource
stored Medplum-style, is kept in its `content` column), while a key that
isn't FHIR at all (a typo, or a stale flattened field like `partof`) fails
with a 422 instead of being silently dropped.

Server-managed `id`/`meta` are stripped before validating — they're ignored
on write, and the server's own values are what the stored resource carries.
`None` / empty lists / empty objects are pruned recursively (FHIR JSON has no
`null` and forbids empty arrays/objects; the database doesn't distinguish
"omitted" from "empty" either).
"""

from __future__ import annotations

from typing import Any

# Never validated from the client body: resourceType is re-stamped, id/meta
# are server-managed and ignored on write.
_SERVER_MANAGED = {"resourceType", "id", "meta"}


def _prune(value: Any) -> Any:
    """Recursively drop None, [], {} (after pruning their own children)."""
    if isinstance(value, dict):
        pruned = {k: _prune(v) for k, v in value.items()}
        return {k: v for k, v in pruned.items() if v is not None and v != [] and v != {}}
    if isinstance(value, list):
        pruned = [_prune(v) for v in value]
        return [v for v in pruned if v is not None and v != [] and v != {}]
    return value


def fhir_create_document(body: dict, resource_type: str) -> dict:
    """The full FHIR resource a CREATE body represents, ready for
    app.fhir.validation.validate_resource()."""
    content = {k: v for k, v in body.items() if k not in _SERVER_MANAGED}
    return {"resourceType": resource_type, **_prune(content)}


def fhir_patch_fragment(body: dict) -> tuple[dict, set[str]]:
    """(fragment, touched) for a PATCH body, to feed
    app.fhir.datatypes.merge_patch_fragment().

    `touched` is every top-level element the request supplied. One that was
    touched but is absent from `fragment` (sent as null or `[]`) is cleared
    by the merge."""
    touched = set(body) - _SERVER_MANAGED
    fragment = _prune({k: body[k] for k in touched})
    return fragment, touched
