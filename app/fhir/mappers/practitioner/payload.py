"""Payload -> FHIR JSON conversion, the mirror image of fhir.py.

fhir.py's to_fhir_practitioner() reads a persisted PractitionerModel (ORM
row, post-insert, with resolved child relationships) and is used for GET
responses. This module reads the *validated Pydantic input schema*
(PractitionerCreateSchema / PractitionerPatchSchema) instead, before
anything is written to the DB, so the result can be fed through
app.fhir.validation.validate_resource() at the service layer — mirrors
app.fhir.mappers.organization.payload's docstring/reasoning exactly.

The two can't fully share code: the input schema has no resolved
{prefix}_type/{prefix}_id for a Reference field yet (that's only known
after RESOURCE_REGISTRY's existence check, which happens at write time) —
only the raw `{prefix}` string the caller supplied, plus
display/identifier-fallback fields. Everything else (coding lists,
HumanName, ContactPoint, Address, Attachment) is structurally identical, so
those builders are deliberately written parallel to fhir.py's,
field-for-field.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.schemas.practitioner.input import (
        PractitionerCreateSchema,
        PractitionerIdentifierInput,
        PractitionerPatchSchema,
        PractitionerQualificationInput,
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
    fallback. Shared by every flattened Reference field on Practitioner's
    input schemas (identifier.assigner, qualification.issuer) — mirrors
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


def payload_identifier(i: PractitionerIdentifierInput) -> dict:
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


def payload_name(n) -> dict:
    entry: dict = {}
    if n.use:
        entry["use"] = fhir_enum(n.use)
    if n.text:
        entry["text"] = n.text
    if n.family:
        entry["family"] = n.family
    if n.given:
        entry["given"] = list(n.given)
    if n.prefix:
        entry["prefix"] = list(n.prefix)
    if n.suffix:
        entry["suffix"] = list(n.suffix)
    period = _period(n.period_start, n.period_end)
    if period:
        entry["period"] = period
    return entry


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


def payload_photo(p) -> dict:
    return {
        k: v
        for k, v in {
            "contentType": p.content_type,
            "language": p.language,
            "data": p.data,
            "url": p.url,
            "size": p.size,
            "hash": p.hash,
            "title": p.title,
            "creation": p.creation.isoformat() if p.creation else None,
        }.items()
        if v is not None
    }


def payload_qualification(q: PractitionerQualificationInput) -> dict:
    entry: dict = {}

    identifiers = [payload_identifier(qi) for qi in (q.identifier or [])]
    if identifiers:
        entry["identifier"] = identifiers

    coding = _coding_list(q.code_coding)
    if coding or q.code_text:
        code_cc: dict = {}
        if coding:
            code_cc["coding"] = coding
        if q.code_text:
            code_cc["text"] = q.code_text
        entry["code"] = code_cc

    period = _period(q.period_start, q.period_end)
    if period:
        entry["period"] = period

    issuer = _reference_from_payload(q, "issuer")
    if issuer:
        entry["issuer"] = issuer

    return entry


def payload_communication(c) -> dict:
    entry: dict = {}
    coding = _coding_list(c.coding)
    if coding:
        entry["coding"] = coding
    if c.text:
        entry["text"] = c.text
    return entry


# Every Practitioner field that's a 0..* list, mapped to the builder that
# renders one of its items — shared by both orchestrators below.
_LIST_FIELDS = {
    "identifier": payload_identifier,
    "name": payload_name,
    "telecom": payload_telecom,
    "address": payload_address,
    "photo": payload_photo,
    "qualification": payload_qualification,
    "communication": payload_communication,
}


def payload_to_fhir_practitioner(payload: PractitionerCreateSchema) -> dict:
    """Full-resource conversion for CREATE: a create payload represents the
    resource's entire initial state, so every field is considered present —
    unlike patch_fragment_to_fhir_practitioner()'s tri-state handling."""
    result: dict = {"resourceType": "Practitioner"}

    if payload.extension:
        result["extension"] = list(payload.extension)
    if payload.active is not None:
        result["active"] = payload.active
    if payload.gender:
        result["gender"] = fhir_enum(payload.gender)
    if payload.birth_date:
        result["birthDate"] = payload.birth_date.isoformat()

    for field, builder in _LIST_FIELDS.items():
        items = [builder(item) for item in (getattr(payload, field, None) or [])]
        items = [item for item in items if item]
        if items:
            result[field] = items

    return result


def patch_fragment_to_fhir_practitioner(
    payload: PractitionerPatchSchema,
) -> tuple[dict, set[str]]:
    """Converts only the fields a PATCH request actually supplied (per
    `model_fields_set`) into a FHIR-shaped fragment, alongside the set of
    top-level FHIR keys the request touched — mirrors
    app.fhir.mappers.organization.payload.patch_fragment_to_fhir_organization's
    docstring/semantics exactly."""
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
    if "gender" in provided:
        touched.add("gender")
        if payload.gender:
            fragment["gender"] = fhir_enum(payload.gender)
    if "birth_date" in provided:
        touched.add("birthDate")
        if payload.birth_date:
            fragment["birthDate"] = payload.birth_date.isoformat()

    for field, builder in _LIST_FIELDS.items():
        if field in provided:
            touched.add(field)
            items = [builder(item) for item in (getattr(payload, field, None) or [])]
            items = [item for item in items if item]
            if items:
                fragment[field] = items

    return fragment, touched
