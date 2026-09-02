from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_split

if TYPE_CHECKING:
    from app.models.practitioner_role import PractitionerRoleModel


def _audit_fields(obj) -> dict:
    """created_at/updated_at/created_by/updated_by — every PractitionerRole
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
    flattened Reference field on PractitionerRole (identifier.assigner,
    practitioner, organization, location, healthcareService, endpoint) —
    mirrors app.fhir.mappers.healthcare_service.plain._plain_reference_fields."""
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


def plain_pr_identifier(i) -> dict:
    """PractitionerRole.identifier (Identifier) → plain snake_case dict.
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


def plain_pr_code(c) -> dict:
    return {
        "id": c.id,
        "coding_system": c.coding_system,
        "coding_version": c.coding_version,
        "coding_code": c.coding_code,
        "coding_display": c.coding_display,
        "text": c.text,
        "coding_user_selected": c.coding_user_selected,
        **_audit_fields(c),
    }


def plain_pr_specialty(sp) -> dict:
    return {
        "id": sp.id,
        "coding_system": sp.coding_system,
        "coding_version": sp.coding_version,
        "coding_code": sp.coding_code,
        "coding_display": sp.coding_display,
        "text": sp.text,
        "coding_user_selected": sp.coding_user_selected,
        **_audit_fields(sp),
    }


def plain_pr_location(loc) -> dict:
    return {
        "id": loc.id,
        **_plain_reference_fields(loc, "reference"),
        **_audit_fields(loc),
    }


def plain_pr_healthcare_service(hs) -> dict:
    return {
        "id": hs.id,
        **_plain_reference_fields(hs, "reference"),
        **_audit_fields(hs),
    }


def plain_pr_telecom(t) -> dict:
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


def plain_pr_available_time(at) -> dict:
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


def plain_pr_not_available(na) -> dict:
    return {
        "id": na.id,
        "description": na.description,
        "during_start": na.during_start.isoformat() if na.during_start else None,
        "during_end": na.during_end.isoformat() if na.during_end else None,
        **_audit_fields(na),
    }


def plain_pr_endpoint(ep) -> dict:
    """PractitionerRole.endpoint (Reference(Endpoint)) → plain snake_case dict.
    Resource-specific because it's a resolved reference with an identifier
    fallback (Endpoint isn't a modeled resource in this system)."""
    return {
        "id": ep.id,
        **_plain_reference_fields(ep, "reference"),
        **_audit_fields(ep),
    }


def to_plain_practitioner_role(pr: PractitionerRoleModel) -> dict:
    return {
        "id": pr.practitioner_role_id,
        "active": pr.active,
        "period_start": pr.period_start.isoformat() if pr.period_start else None,
        "period_end": pr.period_end.isoformat() if pr.period_end else None,
        **_plain_reference_fields(pr, "practitioner"),
        **_plain_reference_fields(pr, "organization"),
        "availability_exceptions": pr.availability_exceptions,
        "identifier": [plain_pr_identifier(i) for i in (pr.identifiers or [])],
        "code": [plain_pr_code(c) for c in (pr.codes or [])],
        "specialty": [plain_pr_specialty(sp) for sp in (pr.specialties or [])],
        "location": [plain_pr_location(loc) for loc in (pr.locations or [])],
        "healthcare_service": [
            plain_pr_healthcare_service(hs) for hs in (pr.healthcare_services or [])
        ],
        "telecom": [plain_pr_telecom(t) for t in (pr.telecoms or [])],
        "available_time": [
            plain_pr_available_time(at) for at in (pr.available_times or [])
        ],
        "not_available": [
            plain_pr_not_available(na) for na in (pr.not_available or [])
        ],
        "endpoint": [plain_pr_endpoint(ep) for ep in (pr.endpoints or [])],
        "org_id": pr.org_id,
        "created_at": pr.created_at.isoformat() if pr.created_at else None,
        "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
        "created_by": pr.created_by,
        "updated_by": pr.updated_by,
    }
