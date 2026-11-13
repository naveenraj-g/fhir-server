"""Row -> FHIR resource for resources stored Medplum-style (the whole
resource in a `content` JSONB column — Organization, Location).

Nothing is rebuilt from columns: `content` is served as-is and the two
server-managed elements are stamped on from the row — `id` (the public
sequence id) and `meta` (from the TenantAuditMixin columns).
"""

from __future__ import annotations

from app.fhir.datatypes import fhir_instant

# Base URL for this server's own, not-yet-formally-registered extensions —
# same convention as scripts/data/profiling/resources/organization/country_in.json's
# StructureDefinition URLs.
EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


def audit_meta(row) -> dict:
    """TenantAuditMixin's columns rendered into Resource.meta. `lastUpdated`
    is Meta's own native field (falling back to created_at for a row never
    updated); org_id/created_by/updated_by/created_at have no native Meta
    field in R4, so they ride as extensions."""
    meta: dict = {}
    if row.updated_at or row.created_at:
        meta["lastUpdated"] = fhir_instant(row.updated_at or row.created_at)

    extensions = []
    if row.tenant_id:
        extensions.append({"url": f"{EXT_BASE}/org-id", "valueString": row.tenant_id})
    if row.created_by:
        extensions.append({"url": f"{EXT_BASE}/created-by", "valueString": row.created_by})
    if row.updated_by:
        extensions.append({"url": f"{EXT_BASE}/updated-by", "valueString": row.updated_by})
    if row.created_at:
        extensions.append(
            {"url": f"{EXT_BASE}/created-at", "valueDateTime": fhir_instant(row.created_at)}
        )
    if extensions:
        meta["extension"] = extensions
    return meta


def content_resource(resource_type: str, public_id, row) -> dict:
    """`{"resourceType", "id", "meta", **row.content}`."""
    result: dict = {"resourceType": resource_type, "id": str(public_id)}
    meta = audit_meta(row)
    if meta:
        result["meta"] = meta
    result.update(row.content or {})
    return result
