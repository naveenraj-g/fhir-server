"""Payload -> FHIR JSON conversion, the mirror image of fhir.py.

fhir.py's to_fhir_healthcare_service() reads a persisted
HealthcareServiceModel (ORM row, post-insert, with resolved child
relationships) and is used for GET responses. This module reads the
*validated Pydantic input schema* (HealthcareServiceCreateSchema /
HealthcareServicePatchSchema) instead, before anything is written to the
DB, so the result can be fed through app.fhir.validation.validate_resource()
at the service layer — mirrors
app.fhir.mappers.organization.payload's docstring/reasoning exactly.

The two can't fully share code: the input schema has no resolved
{prefix}_type/{prefix}_id for a Reference field yet (that's only known
after RESOURCE_REGISTRY's existence check, which happens at write time) —
only the raw `{prefix}` string the caller supplied, plus
display/identifier-fallback fields. Everything else (coding lists,
ContactPoint, CodeableConcept) is structurally identical, so those builders
are deliberately written parallel to fhir.py's, field-for-field.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.schemas.healthcare_service.input import (
        HealthcareServiceCreateSchema,
        HealthcareServiceEligibilityInput,
        HealthcareServiceIdentifierInput,
        HealthcareServicePatchSchema,
    )


def _coding_list(codings) -> list[dict]:
    result = []
    for c in codings or []:
        entry = {
            k: v
            for k, v in {
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "userSelected": c.user_selected,
            }.items()
            if v is not None
        }
        if entry:
            result.append(entry)
    return result


def _cc(codings, text) -> dict:
    """(coding list, text) -> FHIR CodeableConcept dict. Shared by every
    HealthcareService CodeableConcept-list field below — mirrors fhir.py's
    _fhir_cc()."""
    coding = _coding_list(codings)
    entry: dict = {}
    if coding:
        entry["coding"] = coding
    if text:
        entry["text"] = text
    return entry


def _period(start, end) -> dict | None:
    period = {
        k: v
        for k, v in {
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
        }.items()
        if v
    }
    return period or None


def _reference_from_payload(obj, prefix: str) -> dict:
    """Builds a FHIR Reference dict from an input-schema object's raw
    `{prefix}` string (the literal value as submitted — never resolved here)
    plus `{prefix}_display` and the `{prefix}_identifier_*` logical-reference
    fallback. Shared by every flattened Reference field on HealthcareService's
    input schemas (provided_by, identifier.assigner, location.reference,
    coverage_area.reference, endpoint.reference) — mirrors
    app.fhir.mappers.organization.payload._reference_from_payload."""
    raw_reference = getattr(obj, prefix, None)
    display = getattr(obj, f"{prefix}_display", None)

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
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
        period = _period(id_period_start, id_period_end)
        if period:
            identifier["period"] = period
        entry["identifier"] = identifier
    return entry


def payload_identifier(i: HealthcareServiceIdentifierInput) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    type_cc = _cc(i.type_coding, i.type_text)
    if type_cc:
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    period = _period(i.period_start, i.period_end)
    if period:
        entry["period"] = period
    assigner = _reference_from_payload(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def payload_category(c) -> dict:
    return _cc(c.coding, c.text)


def payload_type(t) -> dict:
    return _cc(t.coding, t.text)


def payload_specialty(sp) -> dict:
    return _cc(sp.coding, sp.text)


def payload_location(loc) -> dict:
    return _reference_from_payload(loc, "reference")


def payload_telecom(t) -> dict:
    entry: dict = {}
    if t.system:
        entry["system"] = fhir_enum(t.system)
    if t.value:
        entry["value"] = t.value
    if t.use:
        entry["use"] = fhir_enum(t.use)
    if t.rank is not None:
        entry["rank"] = t.rank
    period = _period(t.period_start, t.period_end)
    if period:
        entry["period"] = period
    return entry


def payload_coverage_area(ca) -> dict:
    return _reference_from_payload(ca, "reference")


def payload_service_provision_code(spc) -> dict:
    return _cc(spc.coding, spc.text)


def payload_eligibility(e: HealthcareServiceEligibilityInput) -> dict:
    entry: dict = {}
    code_cc = _cc(e.code_coding, e.code_text)
    if code_cc:
        entry["code"] = code_cc
    if e.comment:
        entry["comment"] = e.comment
    return entry


def payload_program(p) -> dict:
    return _cc(p.coding, p.text)


def payload_characteristic(c) -> dict:
    return _cc(c.coding, c.text)


def payload_communication(cm) -> dict:
    return _cc(cm.coding, cm.text)


def payload_referral_method(rm) -> dict:
    return _cc(rm.coding, rm.text)


def payload_available_time(at) -> dict:
    entry: dict = {}
    days = [fhir_enum(d) for d in (at.days_of_week or [])]
    if days:
        entry["daysOfWeek"] = days
    if at.all_day is not None:
        entry["allDay"] = at.all_day
    if at.available_start_time:
        entry["availableStartTime"] = at.available_start_time.isoformat()
    if at.available_end_time:
        entry["availableEndTime"] = at.available_end_time.isoformat()
    return entry


def payload_not_available(na) -> dict:
    entry: dict = {}
    if na.description:
        entry["description"] = na.description
    period = _period(na.during_start, na.during_end)
    if period:
        entry["during"] = period
    return entry


def payload_endpoint(ep) -> dict:
    return _reference_from_payload(ep, "reference")


def payload_photo(obj) -> dict:
    """HealthcareService.photo (0..1 Attachment, flattened `photo_*`
    fields) → FHIR camelCase dict — mirrors fhir.py's inline photo dict in
    to_fhir_healthcare_service()."""
    return {
        k: v
        for k, v in {
            "contentType": obj.photo_content_type,
            "language": obj.photo_language,
            "data": obj.photo_data,
            "url": obj.photo_url,
            "size": obj.photo_size,
            "hash": obj.photo_hash,
            "title": obj.photo_title,
            "creation": obj.photo_creation.isoformat() if obj.photo_creation else None,
        }.items()
        if v is not None
    }


# Every HealthcareService field that's a 0..* list, mapped to the builder
# that renders one of its items, and to the FHIR camelCase key it lands
# under — shared by both orchestrators below.
_LIST_FIELDS = {
    "identifier": ("identifier", payload_identifier),
    "category": ("category", payload_category),
    "type": ("type", payload_type),
    "specialty": ("specialty", payload_specialty),
    "location": ("location", payload_location),
    "telecom": ("telecom", payload_telecom),
    "coverage_area": ("coverageArea", payload_coverage_area),
    "service_provision_code": ("serviceProvisionCode", payload_service_provision_code),
    "eligibility": ("eligibility", payload_eligibility),
    "program": ("program", payload_program),
    "characteristic": ("characteristic", payload_characteristic),
    "communication": ("communication", payload_communication),
    "referral_method": ("referralMethod", payload_referral_method),
    "available_time": ("availableTime", payload_available_time),
    "not_available": ("notAvailable", payload_not_available),
    "endpoint": ("endpoint", payload_endpoint),
}

# Field-group membership, used by patch_fragment_to_fhir_healthcare_service()
# to decide whether a PATCH request touched a given flattened group at all
# (any one member being present is enough).
_PROVIDED_BY_FIELDS = {
    "provided_by", "provided_by_display",
    "provided_by_identifier_use", "provided_by_identifier_type_system",
    "provided_by_identifier_type_version", "provided_by_identifier_type_code",
    "provided_by_identifier_type_display", "provided_by_identifier_type_text",
    "provided_by_identifier_type_user_selected", "provided_by_identifier_system",
    "provided_by_identifier_value", "provided_by_identifier_period_start",
    "provided_by_identifier_period_end",
}
_PHOTO_FIELDS = {
    "photo_content_type", "photo_language", "photo_data", "photo_url",
    "photo_size", "photo_hash", "photo_title", "photo_creation",
}


def payload_to_fhir_healthcare_service(payload: HealthcareServiceCreateSchema) -> dict:
    """Full-resource conversion for CREATE: a create payload represents the
    resource's entire initial state, so every field is considered present —
    unlike patch_fragment_to_fhir_healthcare_service()'s tri-state handling."""
    result: dict = {"resourceType": "HealthcareService"}

    provided_by = _reference_from_payload(payload, "provided_by")
    if provided_by:
        result["providedBy"] = provided_by
    if payload.active is not None:
        result["active"] = payload.active
    if payload.name:
        result["name"] = payload.name
    if payload.comment:
        result["comment"] = payload.comment
    if payload.extra_details:
        result["extraDetails"] = payload.extra_details
    photo = payload_photo(payload)
    if photo:
        result["photo"] = photo
    if payload.appointment_required is not None:
        result["appointmentRequired"] = payload.appointment_required
    if payload.availability_exceptions:
        result["availabilityExceptions"] = payload.availability_exceptions

    for field, (fhir_key, builder) in _LIST_FIELDS.items():
        items = [builder(item) for item in (getattr(payload, field, None) or [])]
        items = [item for item in items if item]
        if items:
            result[fhir_key] = items

    return result


def patch_fragment_to_fhir_healthcare_service(
    payload: HealthcareServicePatchSchema,
) -> tuple[dict, set[str]]:
    """Converts only the fields a PATCH request actually supplied (per
    `model_fields_set`) into a FHIR-shaped fragment, alongside the set of
    top-level FHIR keys the request touched — mirrors
    app.fhir.mappers.organization.payload.patch_fragment_to_fhir_organization's
    docstring/semantics exactly."""
    provided = payload.model_fields_set
    fragment: dict = {}
    touched: set[str] = set()

    if provided & _PROVIDED_BY_FIELDS:
        touched.add("providedBy")
        provided_by = _reference_from_payload(payload, "provided_by")
        if provided_by:
            fragment["providedBy"] = provided_by
    if "active" in provided:
        touched.add("active")
        if payload.active is not None:
            fragment["active"] = payload.active
    if "name" in provided:
        touched.add("name")
        if payload.name:
            fragment["name"] = payload.name
    if "comment" in provided:
        touched.add("comment")
        if payload.comment:
            fragment["comment"] = payload.comment
    if "extra_details" in provided:
        touched.add("extraDetails")
        if payload.extra_details:
            fragment["extraDetails"] = payload.extra_details
    if provided & _PHOTO_FIELDS:
        touched.add("photo")
        photo = payload_photo(payload)
        if photo:
            fragment["photo"] = photo
    if "appointment_required" in provided:
        touched.add("appointmentRequired")
        if payload.appointment_required is not None:
            fragment["appointmentRequired"] = payload.appointment_required
    if "availability_exceptions" in provided:
        touched.add("availabilityExceptions")
        if payload.availability_exceptions:
            fragment["availabilityExceptions"] = payload.availability_exceptions

    for field, (fhir_key, builder) in _LIST_FIELDS.items():
        if field in provided:
            touched.add(fhir_key)
            items = [builder(item) for item in (getattr(payload, field, None) or [])]
            items = [item for item in items if item]
            if items:
                fragment[fhir_key] = items

    return fragment, touched
