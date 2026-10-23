from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.practitioner import (
        PractitionerIdentifier,
        PractitionerModel,
        PractitionerQualification,
    )


def _audit_fields(obj) -> dict:
    """created_at/updated_at/created_by/updated_by — every Practitioner
    sub-resource row carries these."""
    return {
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        "created_by": obj.created_by,
        "updated_by": obj.updated_by,
    }


def plain_coding(c) -> dict:
    """One Coding entry (FhirCodingMixin-shaped row) → plain dict. Shared by
    every Practitioner CodeableConcept whose coding is a real 0..* child
    table (identifier.type, qualification.code, communication)."""
    return {
        "id": c.id,
        "system": c.system,
        "version": c.version,
        "code": c.code,
        "display": c.display,
        "user_selected": c.user_selected,
        **_audit_fields(c),
    }


def _plain_reference_fields(obj, prefix: str) -> dict:
    """Raw `{prefix}_reference` string + resolved `{prefix}_type`/`{prefix}_id`/
    `{prefix}_display` + `{prefix}_identifier_*` fallback fields, plus a
    resolved `{prefix}` FHIR-reference-string convenience field. Mirrors
    app.fhir.mappers.organization.plain._plain_reference_fields."""
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    return {
        f"{prefix}_reference": getattr(obj, f"{prefix}_reference", None),
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


def plain_practitioner_identifier(i: PractitionerIdentifier) -> dict:
    return {
        "id": i.id,
        "use": fhir_enum(i.use),
        "type_codings": [plain_coding(c) for c in (i.type_codings or [])],
        "type_text": i.type_text,
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start.isoformat() if i.period_start else None,
        "period_end": i.period_end.isoformat() if i.period_end else None,
        **_plain_reference_fields(i, "assigner"),
        **_audit_fields(i),
    }


def plain_practitioner_name(n) -> dict:
    return {
        "id": n.id,
        "use": fhir_enum(n.use),
        "text": n.text,
        "family": n.family,
        "given": n.given,
        "prefix": n.prefix,
        "suffix": n.suffix,
        "period_start": n.period_start.isoformat() if n.period_start else None,
        "period_end": n.period_end.isoformat() if n.period_end else None,
        **_audit_fields(n),
    }


def plain_practitioner_telecom(t) -> dict:
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


def plain_practitioner_address(a) -> dict:
    return {
        "id": a.id,
        "use": fhir_enum(a.use),
        "type": fhir_enum(a.type),
        "text": a.text,
        "line": a.line,
        "city": a.city,
        "district": a.district,
        "state": a.state,
        "postal_code": a.postal_code,
        "country": a.country,
        "period_start": a.period_start.isoformat() if a.period_start else None,
        "period_end": a.period_end.isoformat() if a.period_end else None,
        **_audit_fields(a),
    }


def plain_practitioner_photo(p) -> dict:
    return {
        "id": p.id,
        "content_type": p.content_type,
        "language": p.language,
        "data": p.data,
        "url": p.url,
        "size": p.size,
        "hash": p.hash,
        "title": p.title,
        "creation": p.creation.isoformat() if p.creation else None,
        **_audit_fields(p),
    }


def plain_practitioner_qualification(q: PractitionerQualification) -> dict:
    return {
        "id": q.id,
        "identifiers": [
            plain_practitioner_identifier(i) for i in (q.identifiers or [])
        ],
        "code_codings": [plain_coding(c) for c in (q.code_codings or [])],
        "code_text": q.code_text,
        "period_start": q.period_start.isoformat() if q.period_start else None,
        "period_end": q.period_end.isoformat() if q.period_end else None,
        **_plain_reference_fields(q, "issuer"),
        **_audit_fields(q),
    }


def plain_practitioner_communication(c) -> dict:
    return {
        "id": c.id,
        "codings": [plain_coding(pc) for pc in (c.codings or [])],
        "text": c.text,
        **_audit_fields(c),
    }


def to_plain_practitioner(p: PractitionerModel) -> dict:
    return {
        "id": p.practitioner_id,
        "user_id": p.user_id,
        "active": p.active,
        "gender": fhir_enum(p.gender),
        "birth_date": p.birth_date.isoformat() if p.birth_date else None,
        "identifier": [plain_practitioner_identifier(i) for i in (p.identifiers or [])],
        "name": [plain_practitioner_name(n) for n in (p.names or [])],
        "telecom": [plain_practitioner_telecom(t) for t in (p.telecoms or [])],
        "address": [plain_practitioner_address(a) for a in (p.addresses or [])],
        "photo": [plain_practitioner_photo(ph) for ph in (p.photos or [])],
        "qualification": [
            plain_practitioner_qualification(q) for q in (p.qualifications or [])
        ],
        "communication": [
            plain_practitioner_communication(c) for c in (p.communications or [])
        ],
        "extension": p.extension or [],
        "org_id": p.tenant_id,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        "created_by": p.created_by,
        "updated_by": p.updated_by,
    }
