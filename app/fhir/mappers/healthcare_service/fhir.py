from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_split, fhir_telecom

if TYPE_CHECKING:
    from app.models.healthcare_service import HealthcareServiceModel


def _fhir_reference(obj, prefix: str) -> dict:
    """Build a FHIR Reference dict for a `{prefix}_type`/`{prefix}_id`/`{prefix}_display`
    resolved reference, with a `{prefix}_identifier_*` logical-reference (Identifier)
    fallback for when the target isn't a resource in this system. Shared by every
    flattened Reference field on HealthcareService (identifier.assigner, providedBy,
    location, coverageArea, endpoint) — mirrors app.fhir.mappers.organization.fhir._fhir_reference."""
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


def fhir_hs_identifier(i) -> dict:
    """HealthcareService.identifier (Identifier) → FHIR camelCase dict.
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


def fhir_hs_category(c) -> dict:
    return _fhir_cc(
        c.coding_system,
        c.coding_version,
        c.coding_code,
        c.coding_display,
        c.text,
        c.coding_user_selected,
    )


def fhir_hs_type(t) -> dict:
    return _fhir_cc(
        t.coding_system,
        t.coding_version,
        t.coding_code,
        t.coding_display,
        t.text,
        t.coding_user_selected,
    )


def fhir_hs_specialty(sp) -> dict:
    return _fhir_cc(
        sp.coding_system,
        sp.coding_version,
        sp.coding_code,
        sp.coding_display,
        sp.text,
        sp.coding_user_selected,
    )


def fhir_hs_location(loc) -> dict:
    return _fhir_reference(loc, "reference")


def fhir_hs_telecom(t) -> dict:
    return fhir_telecom(t)


def fhir_hs_coverage_area(ca) -> dict:
    return _fhir_reference(ca, "reference")


def fhir_hs_service_provision_code(spc) -> dict:
    return _fhir_cc(
        spc.coding_system,
        spc.coding_version,
        spc.coding_code,
        spc.coding_display,
        spc.text,
        spc.coding_user_selected,
    )


def fhir_hs_eligibility(e) -> dict:
    entry: dict = {}
    code_cc = _fhir_cc(
        e.code_system,
        e.code_version,
        e.code_code,
        e.code_display,
        e.code_text,
        e.code_user_selected,
    )
    if code_cc:
        entry["code"] = code_cc
    if e.comment:
        entry["comment"] = e.comment
    return entry


def fhir_hs_program(p) -> dict:
    return _fhir_cc(
        p.coding_system,
        p.coding_version,
        p.coding_code,
        p.coding_display,
        p.text,
        p.coding_user_selected,
    )


def fhir_hs_characteristic(c) -> dict:
    return _fhir_cc(
        c.coding_system,
        c.coding_version,
        c.coding_code,
        c.coding_display,
        c.text,
        c.coding_user_selected,
    )


def fhir_hs_communication(cm) -> dict:
    return _fhir_cc(
        cm.coding_system,
        cm.coding_version,
        cm.coding_code,
        cm.coding_display,
        cm.text,
        cm.coding_user_selected,
    )


def fhir_hs_referral_method(rm) -> dict:
    return _fhir_cc(
        rm.coding_system,
        rm.coding_version,
        rm.coding_code,
        rm.coding_display,
        rm.text,
        rm.coding_user_selected,
    )


def fhir_hs_available_time(at) -> dict:
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


def fhir_hs_not_available(na) -> dict:
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


def fhir_hs_endpoint(ep) -> dict:
    """HealthcareService.endpoint (Reference(Endpoint)) → FHIR camelCase dict.
    Uses the shared resolved-reference-plus-fallback renderer since Endpoint
    isn't a modeled resource — the identifier fallback is often the only
    populated half."""
    return _fhir_reference(ep, "reference")


def to_fhir_healthcare_service(hs: HealthcareServiceModel) -> dict:
    result: dict = {
        "resourceType": "HealthcareService",
        "id": str(hs.healthcare_service_id),
    }

    identifiers = [fhir_hs_identifier(i) for i in (hs.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers

    if hs.active is not None:
        result["active"] = hs.active

    provided_by = _fhir_reference(hs, "provided_by")
    if provided_by:
        result["providedBy"] = provided_by

    categories = [fhir_hs_category(c) for c in (hs.categories or [])]
    if categories:
        result["category"] = categories

    types = [fhir_hs_type(t) for t in (hs.types or [])]
    if types:
        result["type"] = types

    specialties = [fhir_hs_specialty(sp) for sp in (hs.specialties or [])]
    if specialties:
        result["specialty"] = specialties

    locations = [fhir_hs_location(loc) for loc in (hs.locations or [])]
    if locations:
        result["location"] = locations

    if hs.name:
        result["name"] = hs.name

    if hs.comment:
        result["comment"] = hs.comment

    if hs.extra_details:
        result["extraDetails"] = hs.extra_details

    photo = {
        k: v
        for k, v in {
            "contentType": hs.photo_content_type,
            "language": hs.photo_language,
            "data": hs.photo_data,
            "url": hs.photo_url,
            "size": hs.photo_size,
            "hash": hs.photo_hash,
            "title": hs.photo_title,
            "creation": hs.photo_creation.isoformat() if hs.photo_creation else None,
        }.items()
        if v is not None
    }
    if photo:
        result["photo"] = photo

    telecoms = [fhir_hs_telecom(t) for t in (hs.telecoms or [])]
    if telecoms:
        result["telecom"] = telecoms

    coverage_areas = [fhir_hs_coverage_area(ca) for ca in (hs.coverage_areas or [])]
    if coverage_areas:
        result["coverageArea"] = coverage_areas

    spcs = [
        fhir_hs_service_provision_code(spc)
        for spc in (hs.service_provision_codes or [])
    ]
    if spcs:
        result["serviceProvisionCode"] = spcs

    eligibilities = [fhir_hs_eligibility(e) for e in (hs.eligibilities or [])]
    if eligibilities:
        result["eligibility"] = eligibilities

    programs = [fhir_hs_program(p) for p in (hs.programs or [])]
    if programs:
        result["program"] = programs

    chars = [fhir_hs_characteristic(c) for c in (hs.characteristics or [])]
    if chars:
        result["characteristic"] = chars

    comms = [fhir_hs_communication(cm) for cm in (hs.communications or [])]
    if comms:
        result["communication"] = comms

    ref_methods = [fhir_hs_referral_method(rm) for rm in (hs.referral_methods or [])]
    if ref_methods:
        result["referralMethod"] = ref_methods

    if hs.appointment_required is not None:
        result["appointmentRequired"] = hs.appointment_required

    avt = [fhir_hs_available_time(at) for at in (hs.available_times or [])]
    if avt:
        result["availableTime"] = avt

    not_av = [fhir_hs_not_available(na) for na in (hs.not_available or [])]
    if not_av:
        result["notAvailable"] = not_av

    if hs.availability_exceptions:
        result["availabilityExceptions"] = hs.availability_exceptions

    endpoints = [fhir_hs_endpoint(ep) for ep in (hs.endpoints or [])]
    if endpoints:
        result["endpoint"] = endpoints

    return {k: v for k, v in result.items() if v is not None}
