from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_split

if TYPE_CHECKING:
    from app.models.healthcare_service import HealthcareServiceModel


def _audit_fields(obj) -> dict:
    """created_at/updated_at/created_by/updated_by — every HealthcareService
    sub-resource row carries these."""
    return {
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        "created_by": obj.created_by,
        "updated_by": obj.updated_by,
    }


def plain_coding(c) -> dict:
    """One Coding entry (FhirCodingMixin-shaped row) → plain dict. Shared by
    every HealthcareService CodeableConcept-list field's coding[] — all
    real dedicated child tables with the exact same shape — mirrors
    app.fhir.mappers.organization.plain.plain_coding."""
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
    """Flat `{prefix}_type`/`{prefix}_id`/`{prefix}_display` + `{prefix}_identifier_*`
    fallback fields for a resolved-or-logical Reference, plus a resolved
    `{prefix}` FHIR-reference-string convenience field. Shared by every
    flattened Reference field on HealthcareService (identifier.assigner,
    providedBy, location, coverageArea, endpoint) — mirrors
    app.fhir.mappers.organization.plain._plain_reference_fields."""
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


def plain_hs_identifier(i) -> dict:
    """HealthcareService.identifier (Identifier) → plain snake_case dict.
    Resource-specific because assigner is a resolved Reference(Organization)
    with an identifier fallback, and because the row carries an audit
    trail. `type_codings` is a real 0..* child table rather than a single
    flattened coding — mirrors
    app.fhir.mappers.organization.plain.plain_org_identifier."""
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


def plain_hs_category(c) -> dict:
    return {
        "id": c.id,
        "codings": [plain_coding(x) for x in (c.codings or [])],
        "text": c.text,
        **_audit_fields(c),
    }


def plain_hs_type(t) -> dict:
    return {
        "id": t.id,
        "codings": [plain_coding(x) for x in (t.codings or [])],
        "text": t.text,
        **_audit_fields(t),
    }


def plain_hs_specialty(sp) -> dict:
    return {
        "id": sp.id,
        "codings": [plain_coding(x) for x in (sp.codings or [])],
        "text": sp.text,
        **_audit_fields(sp),
    }


def plain_hs_location(loc) -> dict:
    return {
        "id": loc.id,
        **_plain_reference_fields(loc, "reference"),
        **_audit_fields(loc),
    }


def plain_hs_telecom(t) -> dict:
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


def plain_hs_coverage_area(ca) -> dict:
    return {
        "id": ca.id,
        **_plain_reference_fields(ca, "reference"),
        **_audit_fields(ca),
    }


def plain_hs_service_provision_code(spc) -> dict:
    return {
        "id": spc.id,
        "codings": [plain_coding(x) for x in (spc.codings or [])],
        "text": spc.text,
        **_audit_fields(spc),
    }


def plain_hs_eligibility(e) -> dict:
    return {
        "id": e.id,
        "code_codings": [plain_coding(x) for x in (e.code_codings or [])],
        "code_text": e.code_text,
        "comment": e.comment,
        **_audit_fields(e),
    }


def plain_hs_program(p) -> dict:
    return {
        "id": p.id,
        "codings": [plain_coding(x) for x in (p.codings or [])],
        "text": p.text,
        **_audit_fields(p),
    }


def plain_hs_characteristic(c) -> dict:
    return {
        "id": c.id,
        "codings": [plain_coding(x) for x in (c.codings or [])],
        "text": c.text,
        **_audit_fields(c),
    }


def plain_hs_communication(cm) -> dict:
    return {
        "id": cm.id,
        "codings": [plain_coding(x) for x in (cm.codings or [])],
        "text": cm.text,
        **_audit_fields(cm),
    }


def plain_hs_referral_method(rm) -> dict:
    return {
        "id": rm.id,
        "codings": [plain_coding(x) for x in (rm.codings or [])],
        "text": rm.text,
        **_audit_fields(rm),
    }


def plain_hs_available_time(at) -> dict:
    return {
        "id": at.id,
        "days_of_week": fhir_split(at.days_of_week),
        "all_day": at.all_day,
        "available_start_time": at.available_start_time.isoformat()
        if at.available_start_time
        else None,
        "available_end_time": at.available_end_time.isoformat()
        if at.available_end_time
        else None,
        **_audit_fields(at),
    }


def plain_hs_not_available(na) -> dict:
    return {
        "id": na.id,
        "description": na.description,
        "during_start": na.during_start.isoformat() if na.during_start else None,
        "during_end": na.during_end.isoformat() if na.during_end else None,
        **_audit_fields(na),
    }


def plain_hs_endpoint(ep) -> dict:
    """HealthcareService.endpoint (Reference(Endpoint)) → plain snake_case dict.
    Resource-specific because it's a resolved reference with an identifier
    fallback (Endpoint isn't a modeled resource in this system)."""
    return {
        "id": ep.id,
        **_plain_reference_fields(ep, "reference"),
        **_audit_fields(ep),
    }


def to_plain_healthcare_service(hs: HealthcareServiceModel) -> dict:
    return {
        "id": hs.healthcare_service_id,
        "active": hs.active,
        "name": hs.name,
        **_plain_reference_fields(hs, "provided_by"),
        "comment": hs.comment,
        "extra_details": hs.extra_details,
        "photo_content_type": hs.photo_content_type,
        "photo_language": hs.photo_language,
        "photo_data": hs.photo_data,
        "photo_url": hs.photo_url,
        "photo_size": hs.photo_size,
        "photo_hash": hs.photo_hash,
        "photo_title": hs.photo_title,
        "photo_creation": hs.photo_creation.isoformat() if hs.photo_creation else None,
        "appointment_required": hs.appointment_required,
        "availability_exceptions": hs.availability_exceptions,
        "identifier": [plain_hs_identifier(i) for i in (hs.identifiers or [])],
        "category": [plain_hs_category(c) for c in (hs.categories or [])],
        "type": [plain_hs_type(t) for t in (hs.types or [])],
        "specialty": [plain_hs_specialty(sp) for sp in (hs.specialties or [])],
        "location": [plain_hs_location(loc) for loc in (hs.locations or [])],
        "telecom": [plain_hs_telecom(t) for t in (hs.telecoms or [])],
        "coverage_area": [
            plain_hs_coverage_area(ca) for ca in (hs.coverage_areas or [])
        ],
        "service_provision_code": [
            plain_hs_service_provision_code(spc)
            for spc in (hs.service_provision_codes or [])
        ],
        "eligibility": [plain_hs_eligibility(e) for e in (hs.eligibilities or [])],
        "program": [plain_hs_program(p) for p in (hs.programs or [])],
        "characteristic": [
            plain_hs_characteristic(c) for c in (hs.characteristics or [])
        ],
        "communication": [
            plain_hs_communication(cm) for cm in (hs.communications or [])
        ],
        "referral_method": [
            plain_hs_referral_method(rm) for rm in (hs.referral_methods or [])
        ],
        "available_time": [
            plain_hs_available_time(at) for at in (hs.available_times or [])
        ],
        "not_available": [
            plain_hs_not_available(na) for na in (hs.not_available or [])
        ],
        "endpoint": [plain_hs_endpoint(ep) for ep in (hs.endpoints or [])],
        "org_id": hs.tenant_id,
        "created_at": hs.created_at.isoformat() if hs.created_at else None,
        "updated_at": hs.updated_at.isoformat() if hs.updated_at else None,
        "created_by": hs.created_by,
        "updated_by": hs.updated_by,
    }
