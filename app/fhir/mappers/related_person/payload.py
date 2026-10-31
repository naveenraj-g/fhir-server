"""Payload -> FHIR JSON conversion for RelatedPerson.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(RelatedPersonCreateSchema / RelatedPersonPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant, merge_patch_fragment

if TYPE_CHECKING:
    from app.schemas.related_person.input import (
        RelatedPersonAddressInput,
        RelatedPersonCommunicationInput,
        RelatedPersonCreateSchema,
        RelatedPersonIdentifierInput,
        RelatedPersonNameInput,
        RelatedPersonPatchSchema,
        RelatedPersonPhotoInput,
        RelatedPersonRelationshipInput,
        RelatedPersonTelecomInput,
    )

_PATIENT_FIELDS = {"patient", "patient_display"}
_PERIOD_FIELDS = {"period_start", "period_end"}


def _coding_from_payload(c: Any) -> dict:
    if isinstance(c, dict):
        return {
            k: v
            for k, v in {
                "system": c.get("system"),
                "version": c.get("version"),
                "code": c.get("code"),
                "display": c.get("display"),
                "userSelected": c.get("user_selected") or c.get("userSelected"),
            }.items()
            if v is not None
        }
    return {
        k: v
        for k, v in {
            "system": getattr(c, "system", None),
            "version": getattr(c, "version", None),
            "code": getattr(c, "code", None),
            "display": getattr(c, "display", None),
            "userSelected": getattr(c, "user_selected", None),
        }.items()
        if v is not None
    }


def _codeable_concept_from_payload(concept: Any) -> dict | None:
    if not concept:
        return None
    if isinstance(concept, dict):
        codings = [_coding_from_payload(c) for c in (concept.get("coding") or [])]
        codings = [c for c in codings if c]
        text = concept.get("text")
    else:
        codings = [_coding_from_payload(c) for c in (getattr(concept, "coding", None) or [])]
        codings = [c for c in codings if c]
        text = getattr(concept, "text", None)

    result: dict = {}
    if codings:
        result["coding"] = codings
    if text:
        result["text"] = text
    return result or None


def _identifier_from_payload(i: RelatedPersonIdentifierInput) -> dict | None:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    if i.type_coding or i.type_text:
        type_codings = [_coding_from_payload(c) for c in (i.type_coding or [])]
        type_codings = [c for c in type_codings if c]
        type_cc: dict = {}
        if type_codings:
            type_cc["coding"] = type_codings
        if i.type_text:
            type_cc["text"] = i.type_text
        if type_cc:
            entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    if i.period_start or i.period_end:
        period: dict = {}
        if i.period_start:
            period["start"] = fhir_instant(i.period_start)
        if i.period_end:
            period["end"] = fhir_instant(i.period_end)
        entry["period"] = period

    if i.assigner or i.assigner_display:
        assigner: dict = {}
        if i.assigner:
            assigner["reference"] = i.assigner
        if i.assigner_display:
            assigner["display"] = i.assigner_display
        entry["assigner"] = assigner

    return entry or None


def _name_from_payload(n: RelatedPersonNameInput) -> dict | None:
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
        period: dict = {}
        if n.period_start:
            period["start"] = fhir_instant(n.period_start)
        if n.period_end:
            period["end"] = fhir_instant(n.period_end)
        entry["period"] = period
    return entry or None


def _telecom_from_payload(t: RelatedPersonTelecomInput) -> dict | None:
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
        period: dict = {}
        if t.period_start:
            period["start"] = fhir_instant(t.period_start)
        if t.period_end:
            period["end"] = fhir_instant(t.period_end)
        entry["period"] = period
    return entry or None


def _address_from_payload(a: RelatedPersonAddressInput) -> dict | None:
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
        period: dict = {}
        if a.period_start:
            period["start"] = fhir_instant(a.period_start)
        if a.period_end:
            period["end"] = fhir_instant(a.period_end)
        entry["period"] = period
    return entry or None


def _photo_from_payload(p: RelatedPersonPhotoInput) -> dict | None:
    entry: dict = {}
    if p.content_type:
        entry["contentType"] = p.content_type
    if p.language:
        entry["language"] = p.language
    if p.data:
        entry["data"] = p.data
    if p.url:
        entry["url"] = p.url
    if p.size is not None:
        entry["size"] = p.size
    if p.hash:
        entry["hash"] = p.hash
    if p.title:
        entry["title"] = p.title
    if p.creation:
        entry["creation"] = fhir_instant(p.creation)
    return entry or None


def _communication_from_payload(c: RelatedPersonCommunicationInput) -> dict | None:
    lang_codings = [_coding_from_payload(cd) for cd in (c.language_coding or [])]
    lang_codings = [cd for cd in lang_codings if cd]
    lang_cc: dict = {}
    if lang_codings:
        lang_cc["coding"] = lang_codings
    if c.language_text:
        lang_cc["text"] = c.language_text
    if not lang_cc:
        return None
    entry: dict = {"language": lang_cc}
    if c.preferred is not None:
        entry["preferred"] = c.preferred
    return entry


def payload_to_fhir_related_person(payload: RelatedPersonCreateSchema) -> dict:
    """Convert RelatedPersonCreateSchema payload to a FHIR R4 JSON dict."""
    result: dict = {
        "resourceType": "RelatedPerson",
    }

    if payload.extension:
        result["extension"] = list(payload.extension)

    if payload.identifier:
        id_list = [_identifier_from_payload(i) for i in payload.identifier]
        id_list = [i for i in id_list if i]
        if id_list:
            result["identifier"] = id_list

    if payload.active is not None:
        result["active"] = payload.active

    if payload.patient:
        pat_ref: dict = {"reference": payload.patient}
        if payload.patient_display:
            pat_ref["display"] = payload.patient_display
        result["patient"] = pat_ref

    if payload.relationship:
        rel_list = [_codeable_concept_from_payload(r) for r in payload.relationship]
        rel_list = [r for r in rel_list if r]
        if rel_list:
            result["relationship"] = rel_list

    if payload.name:
        name_list = [_name_from_payload(n) for n in payload.name]
        name_list = [n for n in name_list if n]
        if name_list:
            result["name"] = name_list

    if payload.telecom:
        tel_list = [_telecom_from_payload(t) for t in payload.telecom]
        tel_list = [t for t in tel_list if t]
        if tel_list:
            result["telecom"] = tel_list

    if payload.gender:
        result["gender"] = fhir_enum(payload.gender)

    if payload.birth_date:
        result["birthDate"] = payload.birth_date.isoformat()

    if payload.address:
        addr_list = [_address_from_payload(a) for a in payload.address]
        addr_list = [a for a in addr_list if a]
        if addr_list:
            result["address"] = addr_list

    if payload.photo:
        photo_list = [_photo_from_payload(p) for p in payload.photo]
        photo_list = [p for p in photo_list if p]
        if photo_list:
            result["photo"] = photo_list

    if payload.period_start or payload.period_end:
        period: dict = {}
        if payload.period_start:
            period["start"] = fhir_instant(payload.period_start)
        if payload.period_end:
            period["end"] = fhir_instant(payload.period_end)
        result["period"] = period

    if payload.communication:
        comm_list = [_communication_from_payload(c) for c in payload.communication]
        comm_list = [c for c in comm_list if c]
        if comm_list:
            result["communication"] = comm_list

    return result


def patch_fragment_to_fhir_related_person(
    payload: RelatedPersonPatchSchema,
) -> tuple[dict, set[str]]:
    """Convert RelatedPersonPatchSchema to a FHIR fragment and set of touched FHIR keys."""
    provided = payload.model_fields_set
    fragment: dict = {}
    touched: set[str] = set()

    if "extension" in provided:
        touched.add("extension")
        if payload.extension:
            fragment["extension"] = list(payload.extension)

    if "identifier" in provided:
        touched.add("identifier")
        if payload.identifier:
            id_list = [_identifier_from_payload(i) for i in payload.identifier]
            id_list = [i for i in id_list if i]
            if id_list:
                fragment["identifier"] = id_list

    if "active" in provided:
        touched.add("active")
        if payload.active is not None:
            fragment["active"] = payload.active

    if provided & _PATIENT_FIELDS:
        touched.add("patient")
        if payload.patient:
            pat_ref: dict = {"reference": payload.patient}
            if payload.patient_display:
                pat_ref["display"] = payload.patient_display
            fragment["patient"] = pat_ref

    if "relationship" in provided:
        touched.add("relationship")
        if payload.relationship:
            rel_list = [_codeable_concept_from_payload(r) for r in payload.relationship]
            rel_list = [r for r in rel_list if r]
            if rel_list:
                fragment["relationship"] = rel_list

    if "name" in provided:
        touched.add("name")
        if payload.name:
            name_list = [_name_from_payload(n) for n in payload.name]
            name_list = [n for n in name_list if n]
            if name_list:
                fragment["name"] = name_list

    if "telecom" in provided:
        touched.add("telecom")
        if payload.telecom:
            tel_list = [_telecom_from_payload(t) for t in payload.telecom]
            tel_list = [t for t in tel_list if t]
            if tel_list:
                fragment["telecom"] = tel_list

    if "gender" in provided:
        touched.add("gender")
        if payload.gender:
            fragment["gender"] = fhir_enum(payload.gender)

    if "birth_date" in provided:
        touched.add("birthDate")
        if payload.birth_date:
            fragment["birthDate"] = payload.birth_date.isoformat()

    if "address" in provided:
        touched.add("address")
        if payload.address:
            addr_list = [_address_from_payload(a) for a in payload.address]
            addr_list = [a for a in addr_list if a]
            if addr_list:
                fragment["address"] = addr_list

    if "photo" in provided:
        touched.add("photo")
        if payload.photo:
            photo_list = [_photo_from_payload(p) for p in payload.photo]
            photo_list = [p for p in photo_list if p]
            if photo_list:
                fragment["photo"] = photo_list

    if provided & _PERIOD_FIELDS:
        touched.add("period")
        if payload.period_start or payload.period_end:
            period: dict = {}
            if payload.period_start:
                period["start"] = fhir_instant(payload.period_start)
            if payload.period_end:
                period["end"] = fhir_instant(payload.period_end)
            fragment["period"] = period

    if "communication" in provided:
        touched.add("communication")
        if payload.communication:
            comm_list = [_communication_from_payload(c) for c in payload.communication]
            comm_list = [c for c in comm_list if c]
            if comm_list:
                fragment["communication"] = comm_list

    return fragment, touched
