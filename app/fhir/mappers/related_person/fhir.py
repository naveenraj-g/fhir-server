from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.related_person import (
        RelatedPersonAddress,
        RelatedPersonCommunication,
        RelatedPersonIdentifier,
        RelatedPersonModel,
        RelatedPersonName,
        RelatedPersonPhoto,
        RelatedPersonRelationship,
        RelatedPersonTelecom,
    )

_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


def _fhir_coding_list(codings) -> list[dict]:
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


def _fhir_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _fhir_coding_list(codings)
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _fhir_ref(
    ref_raw: str | None,
    ref_type: Any,
    ref_id: int | None,
    display: str | None,
) -> dict | None:
    result: dict = {}
    if ref_raw:
        result["reference"] = ref_raw
    elif ref_type and ref_id:
        result["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        result["display"] = display
    return result or None


def _fhir_identifier(i: RelatedPersonIdentifier) -> dict | None:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    type_cc = _fhir_codeable_concept(getattr(i, "type_codings", None), i.type_text)
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
    assigner = _fhir_ref(
        i.assigner_reference,
        i.assigner_type,
        i.assigner_id,
        i.assigner_display,
    )
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _fhir_name(n: RelatedPersonName) -> dict | None:
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


def _fhir_telecom(t: RelatedPersonTelecom) -> dict | None:
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


def _fhir_address(a: RelatedPersonAddress) -> dict | None:
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


def _fhir_photo(p: RelatedPersonPhoto) -> dict | None:
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


def _fhir_communication(c: RelatedPersonCommunication) -> dict | None:
    lang_cc = _fhir_codeable_concept(
        getattr(c, "language_codings", None), getattr(c, "language_text", None)
    )
    if not lang_cc:
        return None
    entry: dict = {"language": lang_cc}
    if c.preferred is not None:
        entry["preferred"] = c.preferred
    return entry


def _fhir_meta(model: RelatedPersonModel) -> dict:
    meta: dict = {}
    last_updated = model.updated_at or model.created_at
    if last_updated:
        meta["lastUpdated"] = fhir_instant(last_updated)
    extensions: list[dict] = []
    if getattr(model, "tenant_id", None):
        extensions.append(
            {
                "url": f"{_EXT_BASE}/tenant-id",
                "valueString": model.tenant_id,
            }
        )
    if getattr(model, "created_by", None):
        extensions.append(
            {
                "url": f"{_EXT_BASE}/created-by",
                "valueString": model.created_by,
            }
        )
    if getattr(model, "updated_by", None):
        extensions.append(
            {
                "url": f"{_EXT_BASE}/updated-by",
                "valueString": model.updated_by,
            }
        )
    if getattr(model, "created_at", None):
        extensions.append(
            {
                "url": f"{_EXT_BASE}/created-at",
                "valueInstant": fhir_instant(model.created_at),
            }
        )
    if extensions:
        meta["extension"] = extensions
    return meta


def to_fhir_related_person(model: RelatedPersonModel) -> dict:
    """Serialize a RelatedPersonModel to FHIR R4 JSON representation."""
    result: dict = {
        "resourceType": "RelatedPerson",
        "id": str(model.related_person_id),
    }

    meta = _fhir_meta(model)
    if meta:
        result["meta"] = meta

    if model.extension:
        result["extension"] = list(model.extension)

    if model.identifiers:
        id_list = [_fhir_identifier(i) for i in model.identifiers]
        id_list = [i for i in id_list if i]
        if id_list:
            result["identifier"] = id_list

    if model.active is not None:
        result["active"] = model.active

    patient_ref = _fhir_ref(
        model.patient_reference,
        model.patient_type,
        model.patient_id,
        model.patient_display,
    )
    if patient_ref:
        result["patient"] = patient_ref

    if model.relationships:
        rel_list = [
            _fhir_codeable_concept(r.codings, r.text) for r in model.relationships
        ]
        rel_list = [r for r in rel_list if r]
        if rel_list:
            result["relationship"] = rel_list

    if model.names:
        name_list = [_fhir_name(n) for n in model.names]
        name_list = [n for n in name_list if n]
        if name_list:
            result["name"] = name_list

    if model.telecoms:
        telecom_list = [_fhir_telecom(t) for t in model.telecoms]
        telecom_list = [t for t in telecom_list if t]
        if telecom_list:
            result["telecom"] = telecom_list

    if model.gender:
        result["gender"] = fhir_enum(model.gender)

    if model.birth_date:
        result["birthDate"] = model.birth_date.isoformat()

    if model.addresses:
        addr_list = [_fhir_address(a) for a in model.addresses]
        addr_list = [a for a in addr_list if a]
        if addr_list:
            result["address"] = addr_list

    if model.photos:
        photo_list = [_fhir_photo(p) for p in model.photos]
        photo_list = [p for p in photo_list if p]
        if photo_list:
            result["photo"] = photo_list

    if model.period_start or model.period_end:
        period: dict = {}
        if model.period_start:
            period["start"] = fhir_instant(model.period_start)
        if model.period_end:
            period["end"] = fhir_instant(model.period_end)
        result["period"] = period

    if model.communications:
        comm_list = [_fhir_communication(c) for c in model.communications]
        comm_list = [c for c in comm_list if c]
        if comm_list:
            result["communication"] = comm_list

    return result
