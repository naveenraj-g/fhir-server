"""Response examples for the OpenAPI spec, built from each resource's request example.

Without an example, Swagger UI (and anything else reading the spec) invents one from the schema,
which for a fully-typed FHIR resource lists every optional element, including every
`Extension.value[x]` choice. Deriving the response from the request example keeps the two
consistent: what a caller sends is what they get back, plus the server-managed `id` and `meta`.
"""

from __future__ import annotations

_EXTENSION_BASE = "https://fhir-server.dev/fhir/StructureDefinition"
_API_BASE = "http://localhost:8000/api/fhir/v1"
_INSTANT = "2026-01-15T09:30:00Z"


def served_example(resource_type: str, resource_id: str, request: dict) -> dict:
    """The resource as the server returns it: `resourceType`, `id`, `meta`, then the body.

    The `meta` shape matches `app.fhir.mappers.content.audit_meta`.
    """
    audit = [
        ("org-id", "valueString", "org_abc123"),
        ("created-by", "valueString", "user_abc123"),
        ("updated-by", "valueString", "user_abc123"),
        ("created-at", "valueDateTime", _INSTANT),
    ]
    served = {
        "resourceType": resource_type,
        "id": resource_id,
        "meta": {
            "lastUpdated": _INSTANT,
            "extension": [
                {"url": f"{_EXTENSION_BASE}/{name}", key: value}
                for name, key, value in audit
            ],
        },
    }
    # `id` and `meta` are server-managed: a value in the request example is not echoed.
    served.update(
        {k: v for k, v in request.items() if k not in ("resourceType", "id", "meta")}
    )
    return served


def bundle_example(path: str, resource: dict) -> dict:
    """A one-match searchset Bundle holding `resource`; `path` is the router prefix."""
    url = f"{_API_BASE}{path}"
    page = f"{url}?_count=50&_offset=0"
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": 1,
        "link": [{"relation": r, "url": page} for r in ("self", "first", "last")],
        "entry": [
            {
                "fullUrl": f"{url}/{resource['id']}",
                "resource": resource,
                "search": {"mode": "match"},
            }
        ],
    }
