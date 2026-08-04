from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_split

if TYPE_CHECKING:
    from app.models.organization import (
        OrganizationContact,
        OrganizationEndpoint,
        OrganizationIdentifier,
        OrganizationModel,
    )


def _audit_fields(obj) -> dict:
    """created_at/updated_at/created_by/updated_by — every Organization
    sub-resource row carries these."""
    return {
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        "created_by": obj.created_by,
        "updated_by": obj.updated_by,
    }


def _plain_reference_fields(obj, prefix: str) -> dict:
    """Flat `{prefix}_type`/`{prefix}_id`/`{prefix}_display` + `{prefix}_identifier_*`
    fallback fields for a resolved-or-logical Reference, plus a resolved
    `{prefix}` FHIR-reference-string convenience field. Shared by every
    flattened Reference field on Organization (identifier.assigner, partOf,
    endpoint) — mirrors app.fhir.mappers.practitioner.plain._plain_reference_fields."""
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    return {
        prefix: f"{fhir_enum(ref_type)}/{ref_id}" if ref_type and ref_id else None,
        f"{prefix}_type": fhir_enum(ref_type),
        f"{prefix}_id": ref_id,
        f"{prefix}_display": getattr(obj, f"{prefix}_display", None),
        f"{prefix}_identifier_use": fhir_enum(
            getattr(obj, f"{prefix}_identifier_use", None)
        ),
        f"{prefix}_identifier_type_system": getattr(
            obj, f"{prefix}_identifier_type_system", None
        ),
        f"{prefix}_identifier_type_version": getattr(
            obj, f"{prefix}_identifier_type_version", None
        ),
        f"{prefix}_identifier_type_code": getattr(
            obj, f"{prefix}_identifier_type_code", None
        ),
        f"{prefix}_identifier_type_display": getattr(
            obj, f"{prefix}_identifier_type_display", None
        ),
        f"{prefix}_identifier_type_text": getattr(
            obj, f"{prefix}_identifier_type_text", None
        ),
        f"{prefix}_identifier_type_user_selected": getattr(
            obj, f"{prefix}_identifier_type_user_selected", None
        ),
        f"{prefix}_identifier_system": getattr(
            obj, f"{prefix}_identifier_system", None
        ),
        f"{prefix}_identifier_value": getattr(obj, f"{prefix}_identifier_value", None),
        f"{prefix}_identifier_period_start": id_period_start.isoformat()
        if id_period_start
        else None,
        f"{prefix}_identifier_period_end": id_period_end.isoformat()
        if id_period_end
        else None,
    }


def plain_org_identifier(i: OrganizationIdentifier) -> dict:
    """Organization.identifier (Identifier) → plain snake_case dict.
    Resource-specific because assigner is a resolved Reference(Organization)
    with an identifier fallback, and because the row carries an audit trail."""
    return {
        "id": i.id,
        "org_id": i.org_id,
        "use": fhir_enum(i.use),
        "type_system": i.type_system,
        "type_version": i.type_version,
        "type_code": i.type_code,
        "type_display": i.type_display,
        "type_text": i.type_text,
        "type_user_selected": i.type_user_selected,
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start.isoformat() if i.period_start else None,
        "period_end": i.period_end.isoformat() if i.period_end else None,
        **_plain_reference_fields(i, "assigner"),
        **_audit_fields(i),
    }


def plain_org_type(t) -> dict:
    return {
        "id": t.id,
        "coding_system": t.coding_system,
        "coding_version": t.coding_version,
        "coding_code": t.coding_code,
        "coding_display": t.coding_display,
        "text": t.text,
        "coding_user_selected": t.coding_user_selected,
        **_audit_fields(t),
    }


def plain_org_alias(a) -> dict:
    return {
        "id": a.id,
        "value": a.value,
        **_audit_fields(a),
    }


def plain_org_telecom(t) -> dict:
    return {
        "id": t.id,
        "system": fhir_enum(t.system),
        "value": t.value,
        "use": fhir_enum(t.use),
        "rank": t.rank,
        "period_start": t.period_start.isoformat() if t.period_start else None,
        "period_end": t.period_end.isoformat() if t.period_end else None,
        **_audit_fields(t),
    }


def plain_org_address(a) -> dict:
    return {
        "id": a.id,
        "use": fhir_enum(a.use),
        "type": fhir_enum(a.type),
        "text": a.text,
        "line": fhir_split(a.line),
        "city": a.city,
        "district": a.district,
        "state": a.state,
        "postal_code": a.postal_code,
        "country": a.country,
        "period_start": a.period_start.isoformat() if a.period_start else None,
        "period_end": a.period_end.isoformat() if a.period_end else None,
        **_audit_fields(a),
    }


def plain_org_contact_telecom(ct) -> dict:
    return {
        "id": ct.id,
        "system": fhir_enum(ct.system),
        "value": ct.value,
        "use": fhir_enum(ct.use),
        "rank": ct.rank,
        "period_start": ct.period_start.isoformat() if ct.period_start else None,
        "period_end": ct.period_end.isoformat() if ct.period_end else None,
        **_audit_fields(ct),
    }


def plain_org_contact(c: OrganizationContact) -> dict:
    return {
        "id": c.id,
        "purpose_system": c.purpose_system,
        "purpose_code": c.purpose_code,
        "purpose_display": c.purpose_display,
        "purpose_text": c.purpose_text,
        "name_use": fhir_enum(c.name_use),
        "name_text": c.name_text,
        "name_family": c.name_family,
        "name_given": fhir_split(c.name_given),
        "name_prefix": fhir_split(c.name_prefix),
        "name_suffix": fhir_split(c.name_suffix),
        "name_period_start": c.name_period_start.isoformat()
        if c.name_period_start
        else None,
        "name_period_end": c.name_period_end.isoformat() if c.name_period_end else None,
        "address_use": fhir_enum(c.address_use),
        "address_type": fhir_enum(c.address_type),
        "address_text": c.address_text,
        "address_line": fhir_split(c.address_line),
        "address_city": c.address_city,
        "address_district": c.address_district,
        "address_state": c.address_state,
        "address_postal_code": c.address_postal_code,
        "address_country": c.address_country,
        "address_period_start": c.address_period_start.isoformat()
        if c.address_period_start
        else None,
        "address_period_end": c.address_period_end.isoformat()
        if c.address_period_end
        else None,
        "telecoms": [plain_org_contact_telecom(ct) for ct in (c.telecoms or [])],
        **_audit_fields(c),
    }


def plain_org_endpoint(e: OrganizationEndpoint) -> dict:
    """Organization.endpoint (Reference(Endpoint)) → plain snake_case dict.
    Resource-specific because it's a resolved reference with an identifier
    fallback (Endpoint isn't a modeled resource in this system)."""
    return {
        "id": e.id,
        **_plain_reference_fields(e, "reference"),
        **_audit_fields(e),
    }


def to_plain_organization(org: OrganizationModel) -> dict:
    return {
        "id": org.organization_id,
        "active": org.active,
        "name": org.name,
        **_plain_reference_fields(org, "partof"),
        "identifier": [plain_org_identifier(i) for i in (org.identifiers or [])],
        "type": [plain_org_type(t) for t in (org.types or [])],
        "alias": [plain_org_alias(a) for a in (org.aliases or [])],
        "telecom": [plain_org_telecom(t) for t in (org.telecoms or [])],
        "address": [plain_org_address(a) for a in (org.addresses or [])],
        "contact": [plain_org_contact(c) for c in (org.contacts or [])],
        "endpoint": [plain_org_endpoint(e) for e in (org.endpoints or [])],
        "org_id": org.org_id,
        "created_at": org.created_at.isoformat() if org.created_at else None,
        "updated_at": org.updated_at.isoformat() if org.updated_at else None,
        "created_by": org.created_by,
        "updated_by": org.updated_by,
    }
