from __future__ import annotations

from app.fhir.datatypes import fhir_enum, fhir_identifier, fhir_telecom


def _fhir_cc(coding_system, coding_code, coding_display, text) -> dict:
    coding = {k: v for k, v in {
        "system": coding_system,
        "code": coding_code,
        "display": coding_display,
    }.items() if v}
    entry: dict = {}
    if coding:
        entry["coding"] = [coding]
    if text:
        entry["text"] = text
    return entry


def fhir_pr_identifier(i) -> dict:
    return fhir_identifier(i)


def fhir_pr_code(c) -> dict:
    return _fhir_cc(c.coding_system, c.coding_code, c.coding_display, c.text)


def fhir_pr_specialty(sp) -> dict:
    return _fhir_cc(sp.coding_system, sp.coding_code, sp.coding_display, sp.text)


def fhir_pr_location(loc) -> dict:
    ref_type = fhir_enum(loc.reference_type)
    public_id = loc.reference.location_id if loc.reference else loc.reference_id
    entry: dict = {}
    if ref_type and public_id is not None:
        entry["reference"] = f"{ref_type}/{public_id}"
    if loc.reference_display:
        entry["display"] = loc.reference_display
    return entry


def fhir_pr_healthcare_service(hs) -> dict:
    ref_type = fhir_enum(hs.reference_type)
    public_id = hs.reference.healthcare_service_id if hs.reference else hs.reference_id
    entry: dict = {}
    if ref_type and public_id is not None:
        entry["reference"] = f"{ref_type}/{public_id}"
    if hs.reference_display:
        entry["display"] = hs.reference_display
    return entry


def fhir_pr_telecom(t) -> dict:
    return fhir_telecom(t)


def fhir_pr_available_time(at) -> dict:
    entry: dict = {}
    days = [fhir_enum(d) for d in (at.days_of_week or [])]
    if days:
        entry["daysOfWeek"] = days
    if at.all_day is not None:
        entry["allDay"] = at.all_day
    if at.available_start_time:
        entry["availableStartTime"] = at.available_start_time
    if at.available_end_time:
        entry["availableEndTime"] = at.available_end_time
    return entry


def fhir_pr_not_available_time(nat) -> dict:
    entry: dict = {}
    if nat.description:
        entry["description"] = nat.description
    if nat.during_start or nat.during_end:
        entry["during"] = {k: v for k, v in {
            "start": nat.during_start.isoformat() if nat.during_start else None,
            "end": nat.during_end.isoformat() if nat.during_end else None,
        }.items() if v}
    return entry


def fhir_pr_endpoint(ep) -> dict:
    ref_type = fhir_enum(ep.reference_type)
    entry: dict = {}
    if ref_type and ep.reference_id is not None:
        entry["reference"] = f"{ref_type}/{ep.reference_id}"
    if ep.reference_display:
        entry["display"] = ep.reference_display
    return entry


def to_fhir_practitioner_role(pr) -> dict:
    result: dict = {
        "resourceType": "PractitionerRole",
        "id": str(pr.practitioner_role_id),
    }

    if pr.active is not None:
        result["active"] = pr.active

    if pr.period_start or pr.period_end:
        result["period"] = {k: v for k, v in {
            "start": pr.period_start.isoformat() if pr.period_start else None,
            "end": pr.period_end.isoformat() if pr.period_end else None,
        }.items() if v}

    if pr.practitioner and pr.practitioner.practitioner_id:
        prac_ref: dict = {"reference": f"Practitioner/{pr.practitioner.practitioner_id}"}
        if pr.practitioner_display:
            prac_ref["display"] = pr.practitioner_display
        result["practitioner"] = prac_ref

    org_type = fhir_enum(pr.organization_type)
    org_public_id = pr.organization.organization_id if pr.organization else pr.organization_id
    if org_type and org_public_id is not None:
        org_ref: dict = {"reference": f"{org_type}/{org_public_id}"}
        if pr.organization_display:
            org_ref["display"] = pr.organization_display
        result["organization"] = org_ref

    identifiers = [fhir_pr_identifier(i) for i in (pr.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers

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

    available_times = [fhir_pr_available_time(t) for t in (pr.available_times or [])]
    if available_times:
        result["availableTime"] = available_times

    not_available = [fhir_pr_not_available_time(t) for t in (pr.not_available_times or [])]
    if not_available:
        result["notAvailable"] = not_available

    if pr.availability_exceptions:
        result["availabilityExceptions"] = pr.availability_exceptions

    endpoints = [fhir_pr_endpoint(ep) for ep in (pr.endpoints or [])]
    if endpoints:
        result["endpoint"] = endpoints

    return {k: v for k, v in result.items() if v is not None}
