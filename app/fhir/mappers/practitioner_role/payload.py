"""Payload -> FHIR JSON conversion, the mirror image of fhir.py.

fhir.py's to_fhir_practitioner_role() reads a persisted PractitionerRoleModel
(ORM row, post-insert, with resolved child relationships) and is used for GET
responses. This module reads the *validated Pydantic input schema*
(PractitionerRoleCreateSchema / PractitionerRolePatchSchema) instead, before
anything is written to the DB, so the result can be fed through
app.fhir.validation.validate_resource() at the service layer — mirrors
app.fhir.mappers.healthcare_service.payload's docstring/reasoning exactly.

The two can't fully share code: the input schema has no resolved
{prefix}_type/{prefix}_id for a Reference field yet (that's only known after
RESOURCE_REGISTRY's existence check, which happens at write time) — only the
raw `{prefix}` string the caller supplied, plus display/identifier-fallback
fields. Everything else (coding lists, ContactPoint, CodeableConcept) is
structurally identical, so those builders are deliberately written parallel
to fhir.py's, field-for-field.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.schemas.practitioner_role.input import (
        PractitionerRoleCreateSchema,
        PractitionerRoleIdentifierInput,
        PractitionerRolePatchSchema,
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
    PractitionerRole CodeableConcept-list field below — mirrors fhir.py's
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
    fallback. Shared by every flattened Reference field on PractitionerRole's
    input schemas — mirrors
    app.fhir.mappers.healthcare_service.payload._reference_from_payload."""
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


def payload_identifier(i: PractitionerRoleIdentifierInput) -> dict:
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


def payload_code(c) -> dict:
    return _cc(c.coding, c.text)


def payload_specialty(sp) -> dict:
    return _cc(sp.coding, sp.text)


def payload_location(loc) -> dict:
    return _reference_from_payload(loc, "reference")


def payload_healthcare_service(hs) -> dict:
    return _reference_from_payload(hs, "reference")


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


# Every PractitionerRole field that's a 0..* list, mapped to the builder that
# renders one of its items, and to the FHIR camelCase key it lands under —
# shared by both orchestrators below.
_LIST_FIELDS = {
    "identifier": ("identifier", payload_identifier),
    "code": ("code", payload_code),
    "specialty": ("specialty", payload_specialty),
    "location": ("location", payload_location),
    "healthcare_service": ("healthcareService", payload_healthcare_service),
    "telecom": ("telecom", payload_telecom),
    "available_time": ("availableTime", payload_available_time),
    "not_available": ("notAvailable", payload_not_available),
    "endpoint": ("endpoint", payload_endpoint),
}

# Field-group membership, used by patch_fragment_to_fhir_practitioner_role()
# to decide whether a PATCH request touched a given flattened group at all
# (any one member being present is enough).
_PRACTITIONER_FIELDS = {
    "practitioner", "practitioner_display",
    "practitioner_identifier_use", "practitioner_identifier_type_system",
    "practitioner_identifier_type_version", "practitioner_identifier_type_code",
    "practitioner_identifier_type_display", "practitioner_identifier_type_text",
    "practitioner_identifier_type_user_selected", "practitioner_identifier_system",
    "practitioner_identifier_value", "practitioner_identifier_period_start",
    "practitioner_identifier_period_end",
}
_ORGANIZATION_FIELDS = {
    "organization", "organization_display",
    "organization_identifier_use", "organization_identifier_type_system",
    "organization_identifier_type_version", "organization_identifier_type_code",
    "organization_identifier_type_display", "organization_identifier_type_text",
    "organization_identifier_type_user_selected", "organization_identifier_system",
    "organization_identifier_value", "organization_identifier_period_start",
    "organization_identifier_period_end",
}
_PERIOD_FIELDS = {"period_start", "period_end"}


def payload_to_fhir_practitioner_role(payload: PractitionerRoleCreateSchema) -> dict:
    """Full-resource conversion for CREATE: a create payload represents the
    resource's entire initial state, so every field is considered present —
    unlike patch_fragment_to_fhir_practitioner_role()'s tri-state handling."""
    result: dict = {"resourceType": "PractitionerRole"}

    if payload.active is not None:
        result["active"] = payload.active
    period = _period(payload.period_start, payload.period_end)
    if period:
        result["period"] = period
    practitioner = _reference_from_payload(payload, "practitioner")
    if practitioner:
        result["practitioner"] = practitioner
    organization = _reference_from_payload(payload, "organization")
    if organization:
        result["organization"] = organization
    if payload.availability_exceptions:
        result["availabilityExceptions"] = payload.availability_exceptions

    for field, (fhir_key, builder) in _LIST_FIELDS.items():
        items = [builder(item) for item in (getattr(payload, field, None) or [])]
        items = [item for item in items if item]
        if items:
            result[fhir_key] = items

    return result


def patch_fragment_to_fhir_practitioner_role(
    payload: PractitionerRolePatchSchema,
) -> tuple[dict, set[str]]:
    """Converts only the fields a PATCH request actually supplied (per
    `model_fields_set`) into a FHIR-shaped fragment, alongside the set of
    top-level FHIR keys the request touched — mirrors
    app.fhir.mappers.healthcare_service.payload.patch_fragment_to_fhir_healthcare_service's
    docstring/semantics exactly."""
    provided = payload.model_fields_set
    fragment: dict = {}
    touched: set[str] = set()

    if "active" in provided:
        touched.add("active")
        if payload.active is not None:
            fragment["active"] = payload.active
    if provided & _PERIOD_FIELDS:
        touched.add("period")
        period = _period(payload.period_start, payload.period_end)
        if period:
            fragment["period"] = period
    if provided & _PRACTITIONER_FIELDS:
        touched.add("practitioner")
        practitioner = _reference_from_payload(payload, "practitioner")
        if practitioner:
            fragment["practitioner"] = practitioner
    if provided & _ORGANIZATION_FIELDS:
        touched.add("organization")
        organization = _reference_from_payload(payload, "organization")
        if organization:
            fragment["organization"] = organization
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
