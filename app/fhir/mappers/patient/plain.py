from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.patient import (
        PatientContact,
        PatientIdentifier,
        PatientModel,
    )


def _audit_fields(obj) -> dict:
    return {
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        "created_by": obj.created_by,
        "updated_by": obj.updated_by,
    }


def plain_coding(c) -> dict:
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
        f"{prefix}_identifier_period_start": (
            id_period_start.isoformat() if id_period_start else None
        ),
        f"{prefix}_identifier_period_end": (
            id_period_end.isoformat() if id_period_end else None
        ),
    }


def plain_patient_identifier(i: PatientIdentifier) -> dict:
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


def plain_patient_name(n) -> dict:
    return {
        "id": n.id,
        "use": fhir_enum(n.use),
        "text": n.text,
        "family": n.family,
        "given": list(n.given) if n.given else None,
        "prefix": list(n.prefix) if n.prefix else None,
        "suffix": list(n.suffix) if n.suffix else None,
        "period_start": n.period_start.isoformat() if n.period_start else None,
        "period_end": n.period_end.isoformat() if n.period_end else None,
        **_audit_fields(n),
    }


def plain_patient_telecom(t) -> dict:
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


def plain_patient_address(a) -> dict:
    return {
        "id": a.id,
        "use": fhir_enum(a.use),
        "type": fhir_enum(a.type),
        "text": a.text,
        "line": list(a.line) if a.line else None,
        "city": a.city,
        "district": a.district,
        "state": a.state,
        "postal_code": a.postal_code,
        "country": a.country,
        "period_start": a.period_start.isoformat() if a.period_start else None,
        "period_end": a.period_end.isoformat() if a.period_end else None,
        **_audit_fields(a),
    }


def plain_patient_photo(ph) -> dict:
    import base64
    return {
        "id": ph.id,
        "content_type": ph.content_type,
        "language": ph.language,
        "data": base64.b64encode(ph.data).decode("ascii") if ph.data else None,
        "url": ph.url,
        "size": ph.size,
        "hash": base64.b64encode(ph.hash).decode("ascii") if ph.hash else None,
        "title": ph.title,
        "creation": ph.creation.isoformat() if ph.creation else None,
        **_audit_fields(ph),
    }


def plain_patient_contact_relationship(r) -> dict:
    return {
        "id": r.id,
        "text": r.text,
        "codings": [plain_coding(c) for c in (r.codings or [])],
        **_audit_fields(r),
    }


def plain_patient_contact(c: PatientContact) -> dict:
    return {
        "id": c.id,
        "relationships": [
            plain_patient_contact_relationship(r) for r in (c.relationships or [])
        ],
        "gender": fhir_enum(c.gender),
        "name_use": fhir_enum(c.name_use),
        "name_text": c.name_text,
        "name_family": c.name_family,
        "name_given": list(c.name_given) if c.name_given else None,
        "name_prefix": list(c.name_prefix) if c.name_prefix else None,
        "name_suffix": list(c.name_suffix) if c.name_suffix else None,
        "name_period_start": c.name_period_start.isoformat() if c.name_period_start else None,
        "name_period_end": c.name_period_end.isoformat() if c.name_period_end else None,
        "telecom": [plain_patient_telecom(t) for t in (c.telecoms or [])],
        "address_use": fhir_enum(c.use),
        "address_type": fhir_enum(c.type),
        "address_text": c.text,
        "address_line": list(c.line) if c.line else None,
        "address_city": c.city,
        "address_district": c.district,
        "address_state": c.state,
        "address_postal_code": c.postal_code,
        "address_country": c.country,
        "address_period_start": c.period_start.isoformat() if c.period_start else None,
        "address_period_end": c.period_end.isoformat() if c.period_end else None,
        "period_start": c.period_start.isoformat() if c.period_start else None,
        "period_end": c.period_end.isoformat() if c.period_end else None,
        **_plain_reference_fields(c, "organization"),
        **_audit_fields(c),
    }


def plain_patient_communication(c) -> dict:
    return {
        "id": c.id,
        "language_text": c.language_text,
        "language_codings": [plain_coding(pc) for pc in (c.language_codings or [])],
        "preferred": c.preferred,
        **_audit_fields(c),
    }


def plain_patient_general_practitioner(gp) -> dict:
    return {
        "id": gp.id,
        **_plain_reference_fields(gp, "reference"),
        **_audit_fields(gp),
    }


def plain_patient_link(l) -> dict:
    return {
        "id": l.id,
        **_plain_reference_fields(l, "other"),
        "type": fhir_enum(l.type).replace("_", "-") if l.type else None,
        **_audit_fields(l),
    }


def to_plain_patient(p: PatientModel) -> dict:
    ref_type = p.managing_organization_type
    ref_id = p.managing_organization_id
    id_start = p.managing_organization_identifier_period_start if hasattr(p, "managing_organization_identifier_period_start") else None
    id_end = p.managing_organization_identifier_period_end if hasattr(p, "managing_organization_identifier_period_end") else None

    return {
        "id": p.patient_id,
        "user_id": p.user_id,
        "active": p.active,
        "gender": fhir_enum(p.gender),
        "birth_date": p.birth_date.isoformat() if p.birth_date else None,
        "deceased_boolean": p.deceased_boolean,
        "deceased_date_time": (
            p.deceased_date_time.isoformat() if p.deceased_date_time else None
        ),
        "marital_status_text": p.marital_status_text,
        "marital_status_codings": [
            plain_coding(c) for c in (p.marital_status_codings or [])
        ],
        "multiple_birth_boolean": p.multiple_birth_boolean,
        "multiple_birth_integer": p.multiple_birth_integer,
        "managing_organization_reference": p.managing_organization_reference,
        "managing_organization": (
            f"{fhir_enum(ref_type)}/{ref_id}" if ref_type and ref_id else None
        ),
        "managing_organization_type": fhir_enum(ref_type),
        "managing_organization_id": ref_id,
        "managing_organization_display": p.managing_organization_display,
        "managing_organization_identifier_system": p.managing_organization_identifier_system,
        "managing_organization_identifier_value": p.managing_organization_identifier_value,
        "managing_organization_identifier_use": fhir_enum(
            p.managing_organization_identifier_use
        ),
        "managing_organization_identifier_type_text": p.managing_organization_identifier_type_text,
        "identifier": [plain_patient_identifier(i) for i in (p.identifiers or [])],
        "name": [plain_patient_name(n) for n in (p.names or [])],
        "telecom": [plain_patient_telecom(t) for t in (p.telecoms or [])],
        "address": [plain_patient_address(a) for a in (p.addresses or [])],
        "photo": [plain_patient_photo(ph) for ph in (p.photos or [])],
        "contact": [plain_patient_contact(c) for c in (p.contacts or [])],
        "communication": [
            plain_patient_communication(c) for c in (p.communications or [])
        ],
        "general_practitioner": [
            plain_patient_general_practitioner(gp)
            for gp in (p.general_practitioners or [])
        ],
        "link": [plain_patient_link(l) for l in (p.links or [])],
        "extension": p.extension or [],
        "org_id": p.tenant_id,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        "created_by": p.created_by,
        "updated_by": p.updated_by,
    }
