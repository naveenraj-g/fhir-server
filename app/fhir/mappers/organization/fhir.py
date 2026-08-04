from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_split, fhir_telecom

if TYPE_CHECKING:
    from app.models.organization import (
        OrganizationContact,
        OrganizationEndpoint,
        OrganizationIdentifier,
        OrganizationModel,
    )


def _fhir_reference(obj, prefix: str) -> dict:
    """Build a FHIR Reference dict for a `{prefix}_type`/`{prefix}_id`/`{prefix}_display`
    resolved reference, with a `{prefix}_identifier_*` logical-reference (Identifier)
    fallback for when the target isn't a resource in this system. Shared by every
    flattened Reference field on Organization (identifier.assigner, partOf, endpoint)
    — mirrors app.fhir.mappers.practitioner.fhir._fhir_reference."""
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


def fhir_org_identifier(i: OrganizationIdentifier) -> dict:
    """Organization.identifier (Identifier) → FHIR camelCase dict.
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


def fhir_org_type(t) -> dict:
    coding = {
        k: v
        for k, v in {
            "system": t.coding_system,
            "version": t.coding_version,
            "code": t.coding_code,
            "display": t.coding_display,
            "userSelected": t.coding_user_selected,
        }.items()
        if v is not None
    }
    entry: dict = {}
    if coding:
        entry["coding"] = [coding]
    if t.text:
        entry["text"] = t.text
    return entry


def fhir_org_alias(a) -> str:
    return a.value


def fhir_org_telecom(t) -> dict:
    return fhir_telecom(t)


def fhir_org_address(a) -> dict:
    entry: dict = {}
    if a.use:
        entry["use"] = a.use
    if a.type:
        entry["type"] = a.type
    if a.text:
        entry["text"] = a.text
    lines = fhir_split(a.line)
    if lines:
        entry["line"] = lines
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
    if a.period_start or a.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": a.period_start.isoformat() if a.period_start else None,
                "end": a.period_end.isoformat() if a.period_end else None,
            }.items()
            if v
        }
    return entry


def fhir_org_contact(c: OrganizationContact) -> dict:
    entry: dict = {}

    # purpose
    if c.purpose_system or c.purpose_code or c.purpose_text:
        coding = {
            k: v
            for k, v in {
                "system": c.purpose_system,
                "code": c.purpose_code,
                "display": c.purpose_display,
            }.items()
            if v
        }
        purpose_cc: dict = {}
        if coding:
            purpose_cc["coding"] = [coding]
        if c.purpose_text:
            purpose_cc["text"] = c.purpose_text
        if purpose_cc:
            entry["purpose"] = purpose_cc

    # name (HumanName) — columns are prefixed name_*
    if any([c.name_use, c.name_text, c.name_family, c.name_given]):
        name: dict = {}
        if c.name_use:
            name["use"] = fhir_enum(c.name_use)
        if c.name_text:
            name["text"] = c.name_text
        if c.name_family:
            name["family"] = c.name_family
        given = fhir_split(c.name_given)
        if given:
            name["given"] = given
        prefix = fhir_split(c.name_prefix)
        if prefix:
            name["prefix"] = prefix
        suffix = fhir_split(c.name_suffix)
        if suffix:
            name["suffix"] = suffix
        if c.name_period_start or c.name_period_end:
            name["period"] = {
                k: v
                for k, v in {
                    "start": c.name_period_start.isoformat()
                    if c.name_period_start
                    else None,
                    "end": c.name_period_end.isoformat() if c.name_period_end else None,
                }.items()
                if v
            }
        entry["name"] = name

    # telecom
    telecoms = [fhir_telecom(t) for t in (c.telecoms or [])]
    if telecoms:
        entry["telecom"] = telecoms

    # address — columns are prefixed address_*
    if any([c.address_use, c.address_text, c.address_line, c.address_city]):
        addr: dict = {}
        if c.address_use:
            addr["use"] = c.address_use
        if c.address_type:
            addr["type"] = c.address_type
        if c.address_text:
            addr["text"] = c.address_text
        lines = fhir_split(c.address_line)
        if lines:
            addr["line"] = lines
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
        if c.address_period_start or c.address_period_end:
            addr["period"] = {
                k: v
                for k, v in {
                    "start": c.address_period_start.isoformat()
                    if c.address_period_start
                    else None,
                    "end": c.address_period_end.isoformat()
                    if c.address_period_end
                    else None,
                }.items()
                if v
            }
        entry["address"] = addr

    return entry


def fhir_org_endpoint(e: OrganizationEndpoint) -> dict:
    """Organization.endpoint (Reference(Endpoint)) → FHIR camelCase dict.
    Uses the shared resolved-reference-plus-fallback renderer since Endpoint
    isn't a modeled resource — the identifier fallback is often the only
    populated half."""
    return _fhir_reference(e, "reference")


def to_fhir_organization(org: OrganizationModel) -> dict:
    result: dict = {
        "resourceType": "Organization",
        "id": str(org.organization_id),
    }

    if org.active is not None:
        result["active"] = org.active
    if org.name:
        result["name"] = org.name

    identifiers = [fhir_org_identifier(i) for i in (org.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers

    types = [fhir_org_type(t) for t in (org.types or [])]
    if types:
        result["type"] = types

    aliases = [fhir_org_alias(a) for a in (org.aliases or []) if a.value]
    if aliases:
        result["alias"] = aliases

    telecoms = [fhir_org_telecom(t) for t in (org.telecoms or [])]
    if telecoms:
        result["telecom"] = telecoms

    addresses = [fhir_org_address(a) for a in (org.addresses or [])]
    if addresses:
        result["address"] = addresses

    partof = _fhir_reference(org, "partof")
    if partof:
        result["partOf"] = partof

    contacts = [fhir_org_contact(c) for c in (org.contacts or [])]
    if contacts:
        result["contact"] = contacts

    endpoints = [fhir_org_endpoint(e) for e in (org.endpoints or [])]
    if endpoints:
        result["endpoint"] = endpoints

    return {k: v for k, v in result.items() if v is not None}
