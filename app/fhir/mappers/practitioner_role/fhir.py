from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_split, fhir_telecom

if TYPE_CHECKING:
    from app.models.practitioner_role import PractitionerRoleModel


def _fhir_reference(obj, prefix: str) -> dict:
    """Build a FHIR Reference dict for a `{prefix}_type`/`{prefix}_id`/`{prefix}_display`
    resolved reference, with a `{prefix}_identifier_*` logical-reference (Identifier)
    fallback for when the target isn't a resource in this system. Shared by every
    flattened Reference field on PractitionerRole (identifier.assigner, practitioner,
    organization, location, healthcareService, endpoint) — mirrors
    app.fhir.mappers.healthcare_service.fhir._fhir_reference."""
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    entry: dict = {}
    if ref_type and ref_id:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    id_type_system = getattr(obj, f"{prefix}_identifier_type_system", None)
    id_type_version = getattr(obj, f"{prefix}_identifier_type_version", None)
    id_type_code = getattr(obj, f"{prefix}_identifier_type_code", None)
    id_type_display = getattr(obj, f"{prefix}_identifier_type_display", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)
    id_type_user_selected = getattr(
        obj, f"{prefix}_identifier_type_user_selected", None
    )
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)

    if (
        id_use
        or id_type_system
        or id_type_code
        or id_type_text
        or id_system
        or id_value
    ):
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
        if id_type_system or id_type_code or id_type_text:
            type_cc: dict = {}
            if id_type_system or id_type_code:
                type_cc["coding"] = [
                    {
                        k: v
                        for k, v in {
                            "system": id_type_system,
                            "version": id_type_version,
                            "code": id_type_code,
                            "display": id_type_display,
                            "userSelected": id_type_user_selected,
                        }.items()
                        if v is not None
                    }
                ]
            if id_type_text:
                type_cc["text"] = id_type_text
            identifier["type"] = type_cc
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        if id_period_start or id_period_end:
            identifier["period"] = {
                k: v
                for k, v in {
                    "start": id_period_start.isoformat() if id_period_start else None,
                    "end": id_period_end.isoformat() if id_period_end else None,
                }.items()
                if v
            }
        entry["identifier"] = identifier
    return entry


def _fhir_cc(
    coding_system,
    coding_version,
    coding_code,
    coding_display,
    text,
    coding_user_selected,
) -> dict:
    coding = {
        k: v
        for k, v in {
            "system": coding_system,
            "version": coding_version,
            "code": coding_code,
            "display": coding_display,
            "userSelected": coding_user_selected,
        }.items()
        if v is not None
    }
    entry: dict = {}
    if coding:
        entry["coding"] = [coding]
    if text:
        entry["text"] = text
    return entry


def fhir_pr_identifier(i) -> dict:
    """PractitionerRole.identifier (Identifier) → FHIR camelCase dict.
    Resource-specific (not the shared app.fhir.datatypes.fhir_identifier)
    because assigner is a resolved Reference(Organization) with an identifier
    fallback, unlike a flat display string."""
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    if i.type_system or i.type_code or i.type_text:
        type_cc: dict = {}
        if i.type_system or i.type_code:
            type_cc["coding"] = [
                {
                    k: v
                    for k, v in {
                        "system": i.type_system,
                        "version": i.type_version,
                        "code": i.type_code,
                        "display": i.type_display,
                        "userSelected": i.type_user_selected,
                    }.items()
                    if v is not None
                }
            ]
        if i.type_text:
            type_cc["text"] = i.type_text
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    if i.period_start or i.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": i.period_start.isoformat() if i.period_start else None,
                "end": i.period_end.isoformat() if i.period_end else None,
            }.items()
            if v
        }
    assigner = _fhir_reference(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def fhir_pr_code(c) -> dict:
    return _fhir_cc(
        c.coding_system,
        c.coding_version,
        c.coding_code,
        c.coding_display,
        c.text,
        c.coding_user_selected,
    )


def fhir_pr_specialty(sp) -> dict:
    return _fhir_cc(
        sp.coding_system,
        sp.coding_version,
        sp.coding_code,
        sp.coding_display,
        sp.text,
        sp.coding_user_selected,
    )


def fhir_pr_location(loc) -> dict:
    return _fhir_reference(loc, "reference")


def fhir_pr_healthcare_service(hs) -> dict:
    return _fhir_reference(hs, "reference")


def fhir_pr_telecom(t) -> dict:
    return fhir_telecom(t)


def fhir_pr_available_time(at) -> dict:
    entry: dict = {}
    days = fhir_split(at.days_of_week)
    if days:
        entry["daysOfWeek"] = days
    if at.all_day is not None:
        entry["allDay"] = at.all_day
    if at.available_start_time:
        entry["availableStartTime"] = at.available_start_time.isoformat()
    if at.available_end_time:
        entry["availableEndTime"] = at.available_end_time.isoformat()
    return entry


def fhir_pr_not_available(na) -> dict:
    entry: dict = {}
    if na.description:
        entry["description"] = na.description
    if na.during_start or na.during_end:
        entry["during"] = {
            k: v
            for k, v in {
                "start": na.during_start.isoformat() if na.during_start else None,
                "end": na.during_end.isoformat() if na.during_end else None,
            }.items()
            if v
        }
    return entry


def fhir_pr_endpoint(ep) -> dict:
    """PractitionerRole.endpoint (Reference(Endpoint)) → FHIR camelCase dict.
    Uses the shared resolved-reference-plus-fallback renderer since Endpoint
    isn't a modeled resource — the identifier fallback is often the only
    populated half."""
    return _fhir_reference(ep, "reference")


def to_fhir_practitioner_role(pr: PractitionerRoleModel) -> dict:
    result: dict = {
        "resourceType": "PractitionerRole",
        "id": str(pr.practitioner_role_id),
    }

    identifiers = [fhir_pr_identifier(i) for i in (pr.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers

    if pr.active is not None:
        result["active"] = pr.active

    if pr.period_start or pr.period_end:
        result["period"] = {
            k: v
            for k, v in {
                "start": pr.period_start.isoformat() if pr.period_start else None,
                "end": pr.period_end.isoformat() if pr.period_end else None,
            }.items()
            if v
        }

    practitioner = _fhir_reference(pr, "practitioner")
    if practitioner:
        result["practitioner"] = practitioner

    organization = _fhir_reference(pr, "organization")
    if organization:
        result["organization"] = organization

    codes = [fhir_pr_code(c) for c in (pr.codes or [])]
    if codes:
        result["code"] = codes

    specialties = [fhir_pr_specialty(sp) for sp in (pr.specialties or [])]
    if specialties:
        result["specialty"] = specialties

    locations = [fhir_pr_location(loc) for loc in (pr.locations or [])]
    if locations:
        result["location"] = locations

    hcs = [fhir_pr_healthcare_service(hs) for hs in (pr.healthcare_services or [])]
    if hcs:
        result["healthcareService"] = hcs

    telecoms = [fhir_pr_telecom(t) for t in (pr.telecoms or [])]
    if telecoms:
        result["telecom"] = telecoms

    available_times = [fhir_pr_available_time(at) for at in (pr.available_times or [])]
    if available_times:
        result["availableTime"] = available_times

    not_available = [fhir_pr_not_available(na) for na in (pr.not_available or [])]
    if not_available:
        result["notAvailable"] = not_available

    if pr.availability_exceptions:
        result["availabilityExceptions"] = pr.availability_exceptions

    endpoints = [fhir_pr_endpoint(ep) for ep in (pr.endpoints or [])]
    if endpoints:
        result["endpoint"] = endpoints

    return {k: v for k, v in result.items() if v is not None}
