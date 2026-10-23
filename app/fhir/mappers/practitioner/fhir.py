from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.practitioner import (
        PractitionerIdentifier,
        PractitionerModel,
        PractitionerQualification,
    )


def _fhir_coding_list(codings) -> list[dict]:
    """Render a list of FhirCodingMixin-shaped rows as a FHIR `coding[]`
    array — shared by every Practitioner CodeableConcept whose coding is a
    real 0..* child table (identifier.type, qualification.code,
    communication)."""
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


def _fhir_reference(obj, prefix: str) -> dict:
    """Build a FHIR Reference dict for a flattened `{prefix}_*` reference
    group — shared by Practitioner.identifier.assigner and
    Practitioner.qualification.issuer. Mirrors
    app.fhir.mappers.organization.fhir._fhir_reference."""
    raw_reference = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    elif ref_type and ref_id:
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
                    "start": fhir_instant(id_period_start),
                    "end": fhir_instant(id_period_end),
                }.items()
                if v
            }
        entry["identifier"] = identifier
    return entry


def fhir_practitioner_identifier(i: PractitionerIdentifier) -> dict:
    """Practitioner.identifier (Identifier) → FHIR camelCase dict."""
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    coding = _fhir_coding_list(i.type_codings)
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
    if i.period_start or i.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(i.period_start),
                "end": fhir_instant(i.period_end),
            }.items()
            if v
        }
    assigner = _fhir_reference(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def fhir_practitioner_name(n) -> dict:
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
    if n.period_start or n.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(n.period_start),
                "end": fhir_instant(n.period_end),
            }.items()
            if v
        }
    return entry


def fhir_practitioner_telecom(t) -> dict:
    entry: dict = {}
    if t.system:
        entry["system"] = fhir_enum(t.system)
    if t.value:
        entry["value"] = t.value
    if t.use:
        entry["use"] = fhir_enum(t.use)
    if t.rank is not None:
        entry["rank"] = t.rank
    if t.period_start or t.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(t.period_start),
                "end": fhir_instant(t.period_end),
            }.items()
            if v
        }
    return entry


def fhir_practitioner_address(a) -> dict:
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
    if a.period_start or a.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(a.period_start),
                "end": fhir_instant(a.period_end),
            }.items()
            if v
        }
    return entry


def fhir_practitioner_photo(p) -> dict:
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
            "creation": fhir_instant(p.creation),
        }.items()
        if v is not None
    }


def fhir_practitioner_qualification(q: PractitionerQualification) -> dict:
    """Practitioner.qualification (BackboneElement) → FHIR camelCase dict."""
    entry: dict = {}

    identifiers = [fhir_practitioner_identifier(i) for i in (q.identifiers or [])]
    if identifiers:
        entry["identifier"] = identifiers

    coding = _fhir_coding_list(q.code_codings)
    if coding or q.code_text:
        code_cc: dict = {}
        if coding:
            code_cc["coding"] = coding
        if q.code_text:
            code_cc["text"] = q.code_text
        entry["code"] = code_cc

    if q.period_start or q.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(q.period_start),
                "end": fhir_instant(q.period_end),
            }.items()
            if v
        }

    issuer = _fhir_reference(q, "issuer")
    if issuer:
        entry["issuer"] = issuer

    return entry


def fhir_practitioner_communication(c) -> dict:
    entry: dict = {}
    coding = _fhir_coding_list(c.codings)
    if coding:
        entry["coding"] = coding
    if c.text:
        entry["text"] = c.text
    return entry


# Base URL for this server's own, not-yet-formally-registered extensions —
# same convention as app/fhir/mappers/organization/fhir.py's _EXT_BASE.
_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


def _fhir_meta(practitioner: PractitionerModel) -> dict:
    """TenantAuditMixin's columns (tenant_id/created_by/updated_by/
    created_at/updated_at) rendered into Resource.meta — see
    app.fhir.mappers.organization.fhir._fhir_meta's docstring for the full
    reasoning (same pattern, just practitioner-scoped)."""
    meta: dict = {}
    if practitioner.updated_at:
        meta["lastUpdated"] = fhir_instant(practitioner.updated_at)

    extensions = []
    if practitioner.tenant_id:
        extensions.append(
            {"url": f"{_EXT_BASE}/org-id", "valueString": practitioner.tenant_id}
        )
    if practitioner.created_by:
        extensions.append(
            {"url": f"{_EXT_BASE}/created-by", "valueString": practitioner.created_by}
        )
    if practitioner.updated_by:
        extensions.append(
            {"url": f"{_EXT_BASE}/updated-by", "valueString": practitioner.updated_by}
        )
    if practitioner.created_at:
        extensions.append(
            {
                "url": f"{_EXT_BASE}/created-at",
                "valueDateTime": fhir_instant(practitioner.created_at),
            }
        )
    if extensions:
        meta["extension"] = extensions

    return meta


def to_fhir_practitioner(p: PractitionerModel) -> dict:
    result: dict = {
        "resourceType": "Practitioner",
        "id": str(p.practitioner_id),
    }

    meta = _fhir_meta(p)
    if meta:
        result["meta"] = meta

    if p.extension:
        result["extension"] = list(p.extension)

    identifiers = [fhir_practitioner_identifier(i) for i in (p.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers

    if p.active is not None:
        result["active"] = p.active

    names = [fhir_practitioner_name(n) for n in (p.names or [])]
    if names:
        result["name"] = names

    telecoms = [fhir_practitioner_telecom(t) for t in (p.telecoms or [])]
    if telecoms:
        result["telecom"] = telecoms

    addresses = [fhir_practitioner_address(a) for a in (p.addresses or [])]
    if addresses:
        result["address"] = addresses

    if p.gender:
        result["gender"] = fhir_enum(p.gender)
    if p.birth_date:
        result["birthDate"] = p.birth_date.isoformat()

    photos = [fhir_practitioner_photo(ph) for ph in (p.photos or [])]
    if photos:
        result["photo"] = photos

    qualifications = [
        fhir_practitioner_qualification(q) for q in (p.qualifications or [])
    ]
    if qualifications:
        result["qualification"] = qualifications

    communications = [
        fhir_practitioner_communication(c) for c in (p.communications or [])
    ]
    if communications:
        result["communication"] = communications

    return {k: v for k, v in result.items() if v is not None}
