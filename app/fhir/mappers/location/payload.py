"""Payload -> FHIR JSON conversion, the mirror image of fhir.py.

fhir.py's to_fhir_location() reads a persisted LocationModel (ORM row,
post-insert, with resolved child relationships) and is used for GET
responses. This module reads the *validated Pydantic input schema*
(LocationCreateSchema / LocationPatchSchema) instead, before anything is
written to the DB, so the result can be fed through
app.fhir.validation.validate_resource() at the service layer — mirrors
app.fhir.mappers.organization.payload's docstring/reasoning exactly.

The two can't fully share code: the input schema has no resolved
{prefix}_type/{prefix}_id for a Reference field yet (that's only known
after RESOURCE_REGISTRY's existence check, which happens at write time) —
only the raw `{prefix}` string the caller supplied, plus
display/identifier-fallback fields. Everything else (coding lists,
addresses, ContactPoint) is structurally identical, so those builders are
deliberately written parallel to fhir.py's, field-for-field.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_split

if TYPE_CHECKING:
    from app.schemas.location.input import (
        LocationCreateSchema,
        LocationIdentifierInput,
        LocationPatchSchema,
        LocationTypeInput,
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
    fallback. Shared by every flattened Reference field on Location's input
    schemas (managing_organization, part_of, identifier.assigner,
    endpoint.reference) — mirrors
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


def payload_identifier(i: LocationIdentifierInput) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    coding = _coding_list(i.type_coding)
    if coding or i.type_text:
        type_cc: dict = {}
        if coding:
            type_cc["coding"] = coding
        if i.type_text:
            type_cc["text"] = i.type_text
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


def payload_type(t: LocationTypeInput) -> dict:
    entry: dict = {}
    coding = _coding_list(t.coding)
    if coding:
        entry["coding"] = coding
    if t.text:
        entry["text"] = t.text
    return entry


def payload_alias(a) -> str:
    return a.value


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


def payload_hours_of_operation(h) -> dict:
    entry: dict = {}
    days = [fhir_enum(d) for d in (h.days_of_week or [])]
    if days:
        entry["daysOfWeek"] = days
    if h.all_day is not None:
        entry["allDay"] = h.all_day
    if h.opening_time:
        entry["openingTime"] = h.opening_time.isoformat()
    if h.closing_time:
        entry["closingTime"] = h.closing_time.isoformat()
    return entry


def payload_endpoint(e) -> dict:
    return _reference_from_payload(e, "reference")


def payload_address(obj) -> dict:
    """Location.address (0..1 Address, flattened `address_*` fields) → FHIR
    camelCase dict — mirrors fhir.py's fhir_location_address()."""
    entry: dict = {}
    if obj.address_use:
        entry["use"] = fhir_enum(obj.address_use)
    if obj.address_type:
        entry["type"] = fhir_enum(obj.address_type)
    if obj.address_text:
        entry["text"] = obj.address_text
    if obj.address_line:
        entry["line"] = list(obj.address_line)
    if obj.address_city:
        entry["city"] = obj.address_city
    if obj.address_district:
        entry["district"] = obj.address_district
    if obj.address_state:
        entry["state"] = obj.address_state
    if obj.address_postal_code:
        entry["postalCode"] = obj.address_postal_code
    if obj.address_country:
        entry["country"] = obj.address_country
    period = _period(obj.address_period_start, obj.address_period_end)
    if period:
        entry["period"] = period
    return entry


def payload_physical_type(obj) -> dict:
    entry: dict = {}
    coding = _coding_list(obj.physical_type_coding)
    if coding:
        entry["coding"] = coding
    if obj.physical_type_text:
        entry["text"] = obj.physical_type_text
    return entry


def payload_position(obj) -> dict:
    if obj.position_longitude is None or obj.position_latitude is None:
        return {}
    entry: dict = {
        "longitude": obj.position_longitude,
        "latitude": obj.position_latitude,
    }
    if obj.position_altitude is not None:
        entry["altitude"] = obj.position_altitude
    return entry


def payload_operational_status(obj) -> dict:
    return {
        k: v
        for k, v in {
            "system": obj.operational_status_system,
            "version": obj.operational_status_version,
            "code": obj.operational_status_code,
            "display": obj.operational_status_display,
            "userSelected": obj.operational_status_user_selected,
        }.items()
        if v is not None
    }


# Every Location field that's a 0..* list, mapped to the builder that
# renders one of its items — shared by both orchestrators below.
_LIST_FIELDS = {
    "identifier": payload_identifier,
    "type": payload_type,
    "alias": payload_alias,
    "telecom": payload_telecom,
    "hours_of_operation": payload_hours_of_operation,
    "endpoint": payload_endpoint,
}
_LIST_FIELD_TO_FHIR_KEY = {
    "identifier": "identifier",
    "type": "type",
    "alias": "alias",
    "telecom": "telecom",
    "hours_of_operation": "hoursOfOperation",
    "endpoint": "endpoint",
}

# Field-group membership, used by patch_fragment_to_fhir_location() to
# decide whether a PATCH request touched a given flattened group at all
# (any one member being present is enough).
_ADDRESS_FIELDS = {
    "address_use", "address_type", "address_text", "address_line",
    "address_city", "address_district", "address_state",
    "address_postal_code", "address_country",
    "address_period_start", "address_period_end",
}
_PHYSICAL_TYPE_FIELDS = {"physical_type_coding", "physical_type_text"}
_POSITION_FIELDS = {"position_longitude", "position_latitude", "position_altitude"}
_OPERATIONAL_STATUS_FIELDS = {
    "operational_status_system", "operational_status_version",
    "operational_status_code", "operational_status_display",
    "operational_status_user_selected",
}
_MANAGING_ORG_FIELDS = {
    "managing_organization", "managing_organization_display",
    "managing_organization_identifier_use", "managing_organization_identifier_type_system",
    "managing_organization_identifier_type_version", "managing_organization_identifier_type_code",
    "managing_organization_identifier_type_display", "managing_organization_identifier_type_text",
    "managing_organization_identifier_type_user_selected", "managing_organization_identifier_system",
    "managing_organization_identifier_value", "managing_organization_identifier_period_start",
    "managing_organization_identifier_period_end",
}
_PART_OF_FIELDS = {
    "part_of", "part_of_display",
    "part_of_identifier_use", "part_of_identifier_type_system",
    "part_of_identifier_type_version", "part_of_identifier_type_code",
    "part_of_identifier_type_display", "part_of_identifier_type_text",
    "part_of_identifier_type_user_selected", "part_of_identifier_system",
    "part_of_identifier_value", "part_of_identifier_period_start",
    "part_of_identifier_period_end",
}


def payload_to_fhir_location(payload: LocationCreateSchema) -> dict:
    """Full-resource conversion for CREATE: a create payload represents the
    resource's entire initial state, so every field is considered present —
    unlike patch_fragment_to_fhir_location()'s tri-state handling."""
    result: dict = {"resourceType": "Location"}

    if payload.status:
        result["status"] = fhir_enum(payload.status)
    operational_status = payload_operational_status(payload)
    if operational_status:
        result["operationalStatus"] = operational_status
    if payload.name:
        result["name"] = payload.name
    if payload.description:
        result["description"] = payload.description
    if payload.mode:
        result["mode"] = fhir_enum(payload.mode)
    address = payload_address(payload)
    if address:
        result["address"] = address
    physical_type = payload_physical_type(payload)
    if physical_type:
        result["physicalType"] = physical_type
    position = payload_position(payload)
    if position:
        result["position"] = position
    managing_organization = _reference_from_payload(payload, "managing_organization")
    if managing_organization:
        result["managingOrganization"] = managing_organization
    part_of = _reference_from_payload(payload, "part_of")
    if part_of:
        result["partOf"] = part_of
    if payload.availability_exceptions:
        result["availabilityExceptions"] = payload.availability_exceptions

    for field, builder in _LIST_FIELDS.items():
        items = [builder(item) for item in (getattr(payload, field, None) or [])]
        if items:
            result[_LIST_FIELD_TO_FHIR_KEY[field]] = items

    return result


def patch_fragment_to_fhir_location(
    payload: LocationPatchSchema,
) -> tuple[dict, set[str]]:
    """Converts only the fields a PATCH request actually supplied (per
    `model_fields_set`) into a FHIR-shaped fragment, alongside the set of
    top-level FHIR keys the request touched — mirrors
    app.fhir.mappers.organization.payload.patch_fragment_to_fhir_organization's
    docstring/semantics exactly."""
    provided = payload.model_fields_set
    fragment: dict = {}
    touched: set[str] = set()

    if "status" in provided:
        touched.add("status")
        if payload.status:
            fragment["status"] = fhir_enum(payload.status)
    if provided & _OPERATIONAL_STATUS_FIELDS:
        touched.add("operationalStatus")
        operational_status = payload_operational_status(payload)
        if operational_status:
            fragment["operationalStatus"] = operational_status
    if "name" in provided:
        touched.add("name")
        if payload.name:
            fragment["name"] = payload.name
    if "description" in provided:
        touched.add("description")
        if payload.description:
            fragment["description"] = payload.description
    if "mode" in provided:
        touched.add("mode")
        if payload.mode:
            fragment["mode"] = fhir_enum(payload.mode)
    if provided & _ADDRESS_FIELDS:
        touched.add("address")
        address = payload_address(payload)
        if address:
            fragment["address"] = address
    if provided & _PHYSICAL_TYPE_FIELDS:
        touched.add("physicalType")
        physical_type = payload_physical_type(payload)
        if physical_type:
            fragment["physicalType"] = physical_type
    if provided & _POSITION_FIELDS:
        touched.add("position")
        position = payload_position(payload)
        if position:
            fragment["position"] = position
    if provided & _MANAGING_ORG_FIELDS:
        touched.add("managingOrganization")
        managing_organization = _reference_from_payload(payload, "managing_organization")
        if managing_organization:
            fragment["managingOrganization"] = managing_organization
    if provided & _PART_OF_FIELDS:
        touched.add("partOf")
        part_of = _reference_from_payload(payload, "part_of")
        if part_of:
            fragment["partOf"] = part_of
    if "availability_exceptions" in provided:
        touched.add("availabilityExceptions")
        if payload.availability_exceptions:
            fragment["availabilityExceptions"] = payload.availability_exceptions

    for field, builder in _LIST_FIELDS.items():
        if field in provided:
            fhir_key = _LIST_FIELD_TO_FHIR_KEY[field]
            touched.add(fhir_key)
            items = [builder(item) for item in (getattr(payload, field, None) or [])]
            if items:
                fragment[fhir_key] = items

    return fragment, touched
