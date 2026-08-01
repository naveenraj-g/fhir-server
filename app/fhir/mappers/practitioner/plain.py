from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_split

if TYPE_CHECKING:
    from app.models.practitioner.practitioner import (
        PractitionerAddress,
        PractitionerCommunication,
        PractitionerIdentifier,
        PractitionerModel,
        PractitionerName,
        PractitionerPhoto,
        PractitionerQualification,
        PractitionerQualificationIdentifier,
        PractitionerTelecom,
    )


def _audit_fields(obj) -> dict:
    """created_at/updated_at/created_by/updated_by — every Practitioner
    sub-resource row now carries these."""
    return {
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        "created_by": obj.created_by,
        "updated_by": obj.updated_by,
    }


def _plain_reference_fields(obj, prefix: str) -> dict:
    """Flat `{prefix}_type`/`{prefix}_id`/`{prefix}_display` + `{prefix}_identifier_*`
    fallback fields for a resolved-or-logical Reference. Shared by every
    flattened Reference field on Practitioner (identifier.assigner,
    qualification.issuer) — mirrors app.fhir.mappers.patient.plain._plain_reference_fields."""
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)
    return {
        f"{prefix}_type": fhir_enum(getattr(obj, f"{prefix}_type", None)),
        f"{prefix}_id": getattr(obj, f"{prefix}_id", None),
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


def plain_name(n: PractitionerName) -> dict:
    """Practitioner.name (HumanName) → plain snake_case dict. Resource-specific
    because PractitionerName now carries an audit trail."""
    return {
        "id": n.id,
        "org_id": n.org_id,
        "use": fhir_enum(n.use),
        "text": n.text,
        "family": n.family,
        "given": fhir_split(n.given),
        "prefix": fhir_split(n.prefix),
        "suffix": fhir_split(n.suffix),
        "period_start": n.period_start.isoformat() if n.period_start else None,
        "period_end": n.period_end.isoformat() if n.period_end else None,
        **_audit_fields(n),
    }


def plain_identifier(
    i: PractitionerIdentifier | PractitionerQualificationIdentifier,
) -> dict:
    """Practitioner.identifier / qualification.identifier (Identifier) → plain
    snake_case dict. Resource-specific because assigner is a resolved
    Reference(Organization) with an identifier fallback, and because the row
    now carries an audit trail."""
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


def plain_telecom(t: PractitionerTelecom) -> dict:
    """Practitioner.telecom (ContactPoint) → plain snake_case dict.
    Resource-specific because PractitionerTelecom now carries an audit trail."""
    return {
        "id": t.id,
        "org_id": t.org_id,
        "system": fhir_enum(t.system),
        "value": t.value,
        "use": fhir_enum(t.use),
        "rank": t.rank,
        "period_start": t.period_start.isoformat() if t.period_start else None,
        "period_end": t.period_end.isoformat() if t.period_end else None,
        **_audit_fields(t),
    }


def plain_address(a: PractitionerAddress) -> dict:
    """Practitioner.address (Address) → plain snake_case dict.
    Resource-specific because PractitionerAddress now carries an audit trail."""
    return {
        "id": a.id,
        "org_id": a.org_id,
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


def plain_photo(p: PractitionerPhoto) -> dict:
    """Practitioner.photo (Attachment) → plain snake_case dict.
    Resource-specific because PractitionerPhoto now carries an audit trail."""
    return {
        "id": p.id,
        "org_id": p.org_id,
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


def plain_practitioner_communication(cm: PractitionerCommunication) -> dict:
    """communication[] (0..*) CodeableConcept — R4 Practitioner has no `.preferred` (Patient/RelatedPerson-only)."""
    return {
        "id": cm.id,
        "org_id": cm.org_id,
        "language_system": cm.language_system,
        "language_version": cm.language_version,
        "language_code": cm.language_code,
        "language_display": cm.language_display,
        "language_text": cm.language_text,
        "language_user_selected": cm.language_user_selected,
        **_audit_fields(cm),
    }


def plain_qualification(q: PractitionerQualification) -> dict:
    return {
        "id": q.id,
        "org_id": q.org_id,
        "code_system": q.code_system,
        "code_code": q.code_code,
        "code_display": q.code_display,
        "code_text": q.code_text,
        "status_system": q.status_system,
        "status_code": q.status_code,
        "status_display": q.status_display,
        "status_text": q.status_text,
        "period_start": q.period_start.isoformat() if q.period_start else None,
        "period_end": q.period_end.isoformat() if q.period_end else None,
        **_plain_reference_fields(q, "issuer"),
        "identifier": [plain_identifier(qi) for qi in q.identifiers]
        if q.identifiers
        else None,
        **_audit_fields(q),
    }


def to_plain_practitioner(practitioner: PractitionerModel) -> dict:
    result: dict = {
        "id": practitioner.practitioner_id,
        "user_id": practitioner.user_id,
        "org_id": practitioner.org_id,
        "active": practitioner.active,
        "gender": fhir_enum(practitioner.gender) if practitioner.gender else None,
        "birth_date": practitioner.birth_date.isoformat()
        if practitioner.birth_date
        else None,
        "created_at": practitioner.created_at.isoformat()
        if practitioner.created_at
        else None,
        "updated_at": practitioner.updated_at.isoformat()
        if practitioner.updated_at
        else None,
        "created_by": practitioner.created_by,
        "updated_by": practitioner.updated_by,
    }

    if practitioner.names:
        result["name"] = [plain_name(n) for n in practitioner.names]
    if practitioner.identifiers:
        result["identifier"] = [plain_identifier(i) for i in practitioner.identifiers]
    if practitioner.telecoms:
        result["telecom"] = [plain_telecom(t) for t in practitioner.telecoms]
    if practitioner.addresses:
        result["address"] = [plain_address(a) for a in practitioner.addresses]
    if practitioner.photos:
        result["photo"] = [plain_photo(p) for p in practitioner.photos]
    if practitioner.qualifications:
        result["qualification"] = [
            plain_qualification(q) for q in practitioner.qualifications
        ]
    if practitioner.communications:
        result["communication"] = [
            plain_practitioner_communication(c) for c in practitioner.communications
        ]

    return {k: v for k, v in result.items() if v is not None}
