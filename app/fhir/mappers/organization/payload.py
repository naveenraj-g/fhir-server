"""Payload -> FHIR JSON conversion, the mirror image of fhir.py.

fhir.py's to_fhir_organization() reads a persisted OrganizationModel (ORM
row, post-insert, with resolved child relationships) and is used for GET
responses. This module reads the *validated Pydantic input schema*
(OrganizationCreateSchema / OrganizationPatchSchema) instead, before
anything is written to the DB, so the result can be fed through
app.fhir.validation.validate_base_r4() at the service layer — see
docs/architecture/fhir-profiling-and-extensibility-strategy.md.

The two can't fully share code: the input schema has no resolved
{prefix}_type/{prefix}_id for a Reference field yet (that's only known
after RESOURCE_REGISTRY's existence check, which happens at write time) —
only the raw `{prefix}` string the caller supplied, plus
display/identifier-fallback fields. Everything else (coding lists,
addresses, HumanName, ContactPoint) is structurally identical, so those
builders are deliberately written parallel to fhir.py's, field-for-field.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.schemas.organization.input import (
        OrganizationContactInput,
        OrganizationCreateSchema,
        OrganizationEndpointInput,
        OrganizationIdentifierInput,
        OrganizationPatchSchema,
        OrganizationTypeInput,
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
    fallback. Shared by every flattened Reference field on Organization's
    input schemas (partOf, identifier.assigner, endpoint.reference)."""
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


def payload_identifier(i: OrganizationIdentifierInput) -> dict:
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


def payload_type(t: OrganizationTypeInput) -> dict:
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


def payload_address(a) -> dict:
    entry: dict = {}
    if a.use:
        entry["use"] = fhir_enum(a.use)
    if a.type:
        entry["type"] = fhir_enum(a.type)
    if a.text:
        entry["text"] = a.text
    if a.line:
        entry["line"] = list(a.line)
    if a.city:
        entry["city"] = a.city
    if a.district:
        entry["district"] = a.district
    if a.state:
        entry["state"] = a.state
    if a.postal_code:
        entry["postalCode"] = a.postal_code
    if a.country:
        entry["country"] = a.country
    period = _period(a.period_start, a.period_end)
    if period:
        entry["period"] = period
    return entry


def payload_contact(c: OrganizationContactInput) -> dict:
    entry: dict = {}

    coding = _coding_list(c.purpose_coding)
    if coding or c.purpose_text:
        purpose_cc: dict = {}
        if coding:
            purpose_cc["coding"] = coding
        if c.purpose_text:
            purpose_cc["text"] = c.purpose_text
        entry["purpose"] = purpose_cc

    if any([c.name_use, c.name_text, c.name_family, c.name_given]):
        name: dict = {}
        if c.name_use:
            name["use"] = fhir_enum(c.name_use)
        if c.name_text:
            name["text"] = c.name_text
        if c.name_family:
            name["family"] = c.name_family
        if c.name_given:
            name["given"] = list(c.name_given)
        if c.name_prefix:
            name["prefix"] = list(c.name_prefix)
        if c.name_suffix:
            name["suffix"] = list(c.name_suffix)
        period = _period(c.name_period_start, c.name_period_end)
        if period:
            name["period"] = period
        entry["name"] = name

    telecoms = [payload_telecom(t) for t in (c.telecom or [])]
    if telecoms:
        entry["telecom"] = telecoms

    if any([c.address_use, c.address_text, c.address_line, c.address_city]):
        addr: dict = {}
        if c.address_use:
            addr["use"] = fhir_enum(c.address_use)
        if c.address_type:
            addr["type"] = fhir_enum(c.address_type)
        if c.address_text:
            addr["text"] = c.address_text
        if c.address_line:
            addr["line"] = list(c.address_line)
        if c.address_city:
            addr["city"] = c.address_city
        if c.address_district:
            addr["district"] = c.address_district
        if c.address_state:
            addr["state"] = c.address_state
        if c.address_postal_code:
            addr["postalCode"] = c.address_postal_code
        if c.address_country:
            addr["country"] = c.address_country
        period = _period(c.address_period_start, c.address_period_end)
        if period:
            addr["period"] = period
        entry["address"] = addr

    return entry


def payload_endpoint(e: OrganizationEndpointInput) -> dict:
    return _reference_from_payload(e, "reference")


# Shared by both orchestrators below — every Organization field that's a
# 0..* list, mapped to the builder that renders one of its items.
_LIST_FIELDS = {
    "identifier": payload_identifier,
    "type": payload_type,
    "alias": payload_alias,
    "telecom": payload_telecom,
    "address": payload_address,
    "contact": payload_contact,
    "endpoint": payload_endpoint,
}

# partOf's contributing payload field names, used by
# patch_fragment_to_fhir_organization() to decide whether the request
# touched partOf at all (any one of them being present is enough).
_PARTOF_FIELDS = {
    "partof",
    "partof_display",
    "partof_identifier_use",
    "partof_identifier_type_system",
    "partof_identifier_type_version",
    "partof_identifier_type_code",
    "partof_identifier_type_display",
    "partof_identifier_type_text",
    "partof_identifier_type_user_selected",
    "partof_identifier_system",
    "partof_identifier_value",
    "partof_identifier_period_start",
    "partof_identifier_period_end",
}


def payload_to_fhir_organization(payload: OrganizationCreateSchema) -> dict:
    """Full-resource conversion for CREATE: a create payload represents the
    resource's entire initial state, so every field is considered present —
    unlike patch_fragment_to_fhir_organization()'s tri-state handling."""
    result: dict = {"resourceType": "Organization"}

    if payload.extension:
        result["extension"] = list(payload.extension)
    if payload.active is not None:
        result["active"] = payload.active
    if payload.name:
        result["name"] = payload.name

    partof = _reference_from_payload(payload, "partof")
    if partof:
        result["partOf"] = partof

    for field, builder in _LIST_FIELDS.items():
        items = [builder(item) for item in (getattr(payload, field, None) or [])]
        if items:
            result[field] = items

    return result


def patch_fragment_to_fhir_organization(
    payload: OrganizationPatchSchema,
) -> tuple[dict, set[str]]:
    """Converts only the fields a PATCH request actually supplied (per
    `model_fields_set`, same source of truth the repository's own
    `model_dump(exclude_unset=True)` uses) into a FHIR-shaped fragment,
    alongside the set of top-level FHIR keys the request touched.

    The caller merges this fragment over the resource's current full FHIR
    representation (merge_patch_fragment()): a touched key present in the
    fragment overwrites it; a touched key absent from the fragment (a
    scalar explicitly cleared to null, or a list replaced with `[]`) means
    "delete this key"; an untouched key is left alone — exactly
    OrganizationPatchSchema's documented semantics ("every supplied
    sub-resource list ... replaces ... wholesale; omitted lists are left
    untouched")."""
    provided = payload.model_fields_set
    fragment: dict = {}
    touched: set[str] = set()

    if "extension" in provided:
        touched.add("extension")
        if payload.extension:
            fragment["extension"] = list(payload.extension)
    if "active" in provided:
        touched.add("active")
        if payload.active is not None:
            fragment["active"] = payload.active
    if "name" in provided:
        touched.add("name")
        if payload.name:
            fragment["name"] = payload.name

    if provided & _PARTOF_FIELDS:
        touched.add("partOf")
        partof = _reference_from_payload(payload, "partof")
        if partof:
            fragment["partOf"] = partof

    for field, builder in _LIST_FIELDS.items():
        if field in provided:
            touched.add(field)
            items = [builder(item) for item in (getattr(payload, field, None) or [])]
            if items:
                fragment[field] = items

    return fragment, touched


def merge_patch_fragment(existing: dict, fragment: dict, touched: set[str]) -> dict:
    """Shallow-merges a PATCH fragment over the resource's current full FHIR
    representation: every touched key is dropped first (so an explicit
    clear or an empty-list replacement — which the fragment simply omits —
    actually disappears from the merged result), then the fragment's own
    keys are overlaid on top."""
    merged = {k: v for k, v in existing.items() if k not in touched}
    merged.update(fragment)
    return merged
