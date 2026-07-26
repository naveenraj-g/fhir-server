from __future__ import annotations

from app.fhir.datatypes import fhir_enum, plain_identifier


def plain_pr_identifier(i) -> dict:
    return {"id": i.id, **plain_identifier(i)}


def plain_pr_code(c) -> dict:
    return {
        "id": c.id,
        "coding_system": c.coding_system,
        "coding_code": c.coding_code,
        "coding_display": c.coding_display,
        "text": c.text,
    }


def plain_pr_specialty(sp) -> dict:
    return {
        "id": sp.id,
        "coding_system": sp.coding_system,
        "coding_code": sp.coding_code,
        "coding_display": sp.coding_display,
        "text": sp.text,
    }


def plain_pr_location(loc) -> dict:
    return {
        "id": loc.id,
        "reference_type": fhir_enum(loc.reference_type),
        "reference_id": loc.reference.location_id if loc.reference else loc.reference_id,
        "reference_display": loc.reference_display,
    }


def plain_pr_healthcare_service(hs) -> dict:
    return {
        "id": hs.id,
        "reference_type": fhir_enum(hs.reference_type),
        "reference_id": hs.reference.healthcare_service_id if hs.reference else hs.reference_id,
        "reference_display": hs.reference_display,
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
    }


def plain_pr_available_time(at) -> dict:
    return {
        "id": at.id,
        "days_of_week": [fhir_enum(d) for d in (at.days_of_week or [])],
        "all_day": at.all_day,
        "available_start_time": at.available_start_time,
        "available_end_time": at.available_end_time,
    }


def plain_pr_not_available_time(nat) -> dict:
    return {
        "id": nat.id,
        "description": nat.description,
        "during_start": nat.during_start.isoformat() if nat.during_start else None,
        "during_end": nat.during_end.isoformat() if nat.during_end else None,
    }


def plain_pr_endpoint(ep) -> dict:
    return {
        "id": ep.id,
        "reference_type": fhir_enum(ep.reference_type),
        "reference_id": ep.reference_id,
        "reference_display": ep.reference_display,
    }


def to_plain_practitioner_role(pr) -> dict:
    return {
        "id": pr.practitioner_role_id,
        "active": pr.active,
        "period_start": pr.period_start.isoformat() if pr.period_start else None,
        "period_end": pr.period_end.isoformat() if pr.period_end else None,
        "practitioner_id": pr.practitioner.practitioner_id if pr.practitioner else None,
        "practitioner_display": pr.practitioner_display,
        "organization_type": fhir_enum(pr.organization_type),
        "organization_id": pr.organization.organization_id if pr.organization else pr.organization_id,
        "organization_display": pr.organization_display,
        "availability_exceptions": pr.availability_exceptions,
        "identifier": [plain_pr_identifier(i) for i in (pr.identifiers or [])],
        "code": [plain_pr_code(c) for c in (pr.codes or [])],
        "specialty": [plain_pr_specialty(sp) for sp in (pr.specialties or [])],
        "location": [plain_pr_location(loc) for loc in (pr.locations or [])],
        "healthcare_service": [plain_pr_healthcare_service(hs) for hs in (pr.healthcare_services or [])],
        "telecom": [plain_pr_telecom(t) for t in (pr.telecoms or [])],
        "available_time": [plain_pr_available_time(t) for t in (pr.available_times or [])],
        "not_available": [plain_pr_not_available_time(t) for t in (pr.not_available_times or [])],
        "endpoint": [plain_pr_endpoint(ep) for ep in (pr.endpoints or [])],
        "user_id": pr.user_id,
        "org_id": pr.org_id,
        "created_at": pr.created_at.isoformat() if pr.created_at else None,
        "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
        "created_by": pr.created_by,
        "updated_by": pr.updated_by,
    }
