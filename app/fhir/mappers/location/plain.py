from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_split

if TYPE_CHECKING:
    from app.models.location import (
        LocationEndpoint,
        LocationHoursOfOperation,
        LocationIdentifier,
        LocationModel,
    )


def _audit_fields(obj) -> dict:
    """created_at/updated_at/created_by/updated_by — every Location
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
    flattened Reference field on Location (identifier.assigner,
    managingOrganization, partOf, endpoint) — mirrors
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


def plain_location_identifier(i: LocationIdentifier) -> dict:
    """Location.identifier (Identifier) → plain snake_case dict. Resource-specific
    because assigner is a resolved Reference(Organization) with an identifier
    fallback, and because the row carries an audit trail."""
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


def plain_location_type(t) -> dict:
    """Location.type (CodeableConcept) → plain snake_case dict."""
    return {
        "id": t.id,
        "org_id": t.org_id,
        "coding_system": t.coding_system,
        "coding_version": t.coding_version,
        "coding_code": t.coding_code,
        "coding_display": t.coding_display,
        "text": t.text,
        "coding_user_selected": t.coding_user_selected,
        **_audit_fields(t),
    }


def plain_location_alias(a) -> dict:
    """Location.alias → plain snake_case dict. Unlike the FHIR mapper (which
    collapses the row to a bare string), the plain form keeps the row id so
    callers can target it with a sub-resource DELETE."""
    return {
        "id": a.id,
        "org_id": a.org_id,
        "value": a.value,
        **_audit_fields(a),
    }


def plain_location_telecom(t) -> dict:
    """Location.telecom (ContactPoint) → plain snake_case dict."""
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


def plain_location_hours_of_operation(h: LocationHoursOfOperation) -> dict:
    """Location.hoursOfOperation (BackboneElement) → plain snake_case dict.
    `days_of_week` is split back out of the comma-separated column into a real
    list, so the plain form and the FHIR form agree."""
    return {
        "id": h.id,
        "org_id": h.org_id,
        "days_of_week": fhir_split(h.days_of_week),
        "all_day": h.all_day,
        "opening_time": h.opening_time.isoformat() if h.opening_time else None,
        "closing_time": h.closing_time.isoformat() if h.closing_time else None,
        **_audit_fields(h),
    }


def plain_location_endpoint(e: LocationEndpoint) -> dict:
    """Location.endpoint (Reference(Endpoint)) → plain snake_case dict."""
    return {
        "id": e.id,
        "org_id": e.org_id,
        **_plain_reference_fields(e, "reference"),
        **_audit_fields(e),
    }


def to_plain_location(loc: LocationModel) -> dict:
    return {
        "id": loc.location_id,
        "status": fhir_enum(loc.status),
        "operational_status_system": loc.operational_status_system,
        "operational_status_version": loc.operational_status_version,
        "operational_status_code": loc.operational_status_code,
        "operational_status_display": loc.operational_status_display,
        "operational_status_user_selected": loc.operational_status_user_selected,
        "name": loc.name,
        "description": loc.description,
        "mode": fhir_enum(loc.mode),
        # address (0..1) is flattened onto the parent row — address_line is
        # split back out of its comma-separated column, matching the FHIR form.
        "address_use": fhir_enum(loc.address_use),
        "address_type": fhir_enum(loc.address_type),
        "address_text": loc.address_text,
        "address_line": fhir_split(loc.address_line),
        "address_city": loc.address_city,
        "address_district": loc.address_district,
        "address_state": loc.address_state,
        "address_postal_code": loc.address_postal_code,
        "address_country": loc.address_country,
        "address_period_start": loc.address_period_start.isoformat()
        if loc.address_period_start
        else None,
        "address_period_end": loc.address_period_end.isoformat()
        if loc.address_period_end
        else None,
        "physical_type_system": loc.physical_type_system,
        "physical_type_version": loc.physical_type_version,
        "physical_type_code": loc.physical_type_code,
        "physical_type_display": loc.physical_type_display,
        "physical_type_text": loc.physical_type_text,
        "physical_type_user_selected": loc.physical_type_user_selected,
        "position_longitude": loc.position_longitude,
        "position_latitude": loc.position_latitude,
        "position_altitude": loc.position_altitude,
        **_plain_reference_fields(loc, "managing_organization"),
        **_plain_reference_fields(loc, "part_of"),
        "availability_exceptions": loc.availability_exceptions,
        "identifier": [plain_location_identifier(i) for i in (loc.identifiers or [])],
        "type": [plain_location_type(t) for t in (loc.types or [])],
        "alias": [plain_location_alias(a) for a in (loc.aliases or [])],
        "telecom": [plain_location_telecom(t) for t in (loc.telecoms or [])],
        "hours_of_operation": [
            plain_location_hours_of_operation(h)
            for h in (loc.hours_of_operation or [])
        ],
        "endpoint": [plain_location_endpoint(e) for e in (loc.endpoints or [])],
        "org_id": loc.org_id,
        "created_at": loc.created_at.isoformat() if loc.created_at else None,
        "updated_at": loc.updated_at.isoformat() if loc.updated_at else None,
        "created_by": loc.created_by,
        "updated_by": loc.updated_by,
    }
