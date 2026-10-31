from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.specimen import SpecimenModel

_COMPARATOR_SYMBOLS = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}


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


def fhir_specimen_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _fhir_coding_list(codings)
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _fhir_reference_with_identifier_fallback(obj, prefix: str) -> dict | None:
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
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)

    if id_use or id_system or id_value or id_type_text:
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        if id_type_text:
            identifier["type"] = {"text": id_type_text}
        entry["identifier"] = identifier

    return entry or None


def _fhir_duration(obj, prefix: str) -> dict | None:
    value = getattr(obj, f"{prefix}_value", None)
    if value is None:
        return None
    comparator = getattr(obj, f"{prefix}_comparator", None)
    result = {
        k: v
        for k, v in {
            "value": float(value),
            "comparator": _COMPARATOR_SYMBOLS.get(fhir_enum(comparator)) if comparator else None,
            "unit": getattr(obj, f"{prefix}_unit", None),
            "system": getattr(obj, f"{prefix}_system", None),
            "code": getattr(obj, f"{prefix}_code", None),
        }.items()
        if v is not None
    }
    return result or None


def _fhir_simple_quantity(obj, prefix: str) -> dict | None:
    value = getattr(obj, f"{prefix}_value", None)
    if value is None:
        return None
    result = {
        k: v
        for k, v in {
            "value": float(value),
            "unit": getattr(obj, f"{prefix}_unit", None),
            "system": getattr(obj, f"{prefix}_system", None),
            "code": getattr(obj, f"{prefix}_code", None),
        }.items()
        if v is not None
    }
    return result or None


def fhir_specimen_identifier(i) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value

    type_codings = _fhir_coding_list(getattr(i, "type_codings", []))
    if type_codings or i.type_text:
        t: dict = {}
        if type_codings:
            t["coding"] = type_codings
        if i.type_text:
            t["text"] = i.type_text
        entry["type"] = t

    if i.period_start or i.period_end:
        p: dict = {}
        if i.period_start:
            p["start"] = fhir_instant(i.period_start)
        if i.period_end:
            p["end"] = fhir_instant(i.period_end)
        entry["period"] = p

    assigner = _fhir_reference_with_identifier_fallback(i, "assigner")
    if assigner:
        entry["assigner"] = assigner

    return entry


def fhir_specimen_accession_identifier(model: SpecimenModel) -> dict | None:
    entry: dict = {}
    if model.accession_identifier_use:
        entry["use"] = fhir_enum(model.accession_identifier_use)
    if model.accession_identifier_system:
        entry["system"] = model.accession_identifier_system
    if model.accession_identifier_value:
        entry["value"] = model.accession_identifier_value

    type_codings = _fhir_coding_list(getattr(model, "accession_identifier_type_codings", []))
    if type_codings or model.accession_identifier_type_text:
        t: dict = {}
        if type_codings:
            t["coding"] = type_codings
        if model.accession_identifier_type_text:
            t["text"] = model.accession_identifier_type_text
        entry["type"] = t

    if model.accession_identifier_period_start or model.accession_identifier_period_end:
        p: dict = {}
        if model.accession_identifier_period_start:
            p["start"] = fhir_instant(model.accession_identifier_period_start)
        if model.accession_identifier_period_end:
            p["end"] = fhir_instant(model.accession_identifier_period_end)
        entry["period"] = p

    assigner = _fhir_reference_with_identifier_fallback(model, "accession_identifier_assigner")
    if assigner:
        entry["assigner"] = assigner

    return entry or None


def fhir_specimen_collection(model: SpecimenModel) -> dict | None:
    entry: dict = {}

    collector = _fhir_reference_with_identifier_fallback(model, "collection_collector")
    if collector:
        entry["collector"] = collector

    if model.collection_collected_date_time:
        entry["collectedDateTime"] = fhir_instant(model.collection_collected_date_time)
    elif model.collection_collected_period_start or model.collection_collected_period_end:
        p: dict = {}
        if model.collection_collected_period_start:
            p["start"] = fhir_instant(model.collection_collected_period_start)
        if model.collection_collected_period_end:
            p["end"] = fhir_instant(model.collection_collected_period_end)
        entry["collectedPeriod"] = p

    duration = _fhir_duration(model, "collection_duration")
    if duration:
        entry["duration"] = duration

    quantity = _fhir_simple_quantity(model, "collection_quantity")
    if quantity:
        entry["quantity"] = quantity

    method = fhir_specimen_codeable_concept(
        model.collection_method_codings, model.collection_method_text
    )
    if method:
        entry["method"] = method

    body_site = fhir_specimen_codeable_concept(
        model.collection_body_site_codings, model.collection_body_site_text
    )
    if body_site:
        entry["bodySite"] = body_site

    fasting_concept = fhir_specimen_codeable_concept(
        model.collection_fasting_status_codings, model.collection_fasting_status_text
    )
    if fasting_concept:
        entry["fastingStatusCodeableConcept"] = fasting_concept
    elif model.collection_fasting_status_duration_value is not None:
        fasting_dur = _fhir_duration(model, "collection_fasting_status_duration")
        if fasting_dur:
            entry["fastingStatusDuration"] = fasting_dur

    return entry or None


def fhir_specimen_processing(p) -> dict:
    entry: dict = {}
    if p.description:
        entry["description"] = p.description

    procedure = fhir_specimen_codeable_concept(p.procedure_codings, p.procedure_text)
    if procedure:
        entry["procedure"] = procedure

    additives = [
        _fhir_reference_with_identifier_fallback(a, "reference")
        for a in (p.additives or [])
    ]
    additives = [a for a in additives if a]
    if additives:
        entry["additive"] = additives

    if p.time_date_time:
        entry["timeDateTime"] = fhir_instant(p.time_date_time)
    elif p.time_period_start or p.time_period_end:
        period: dict = {}
        if p.time_period_start:
            period["start"] = fhir_instant(p.time_period_start)
        if p.time_period_end:
            period["end"] = fhir_instant(p.time_period_end)
        entry["timePeriod"] = period

    return entry


def fhir_specimen_container_identifier(i) -> dict:
    return fhir_specimen_identifier(i)


def fhir_specimen_container(c) -> dict:
    entry: dict = {}

    identifiers = [
        fhir_specimen_container_identifier(i)
        for i in (c.identifiers or [])
    ]
    identifiers = [i for i in identifiers if i]
    if identifiers:
        entry["identifier"] = identifiers

    if c.description:
        entry["description"] = c.description

    ctype = fhir_specimen_codeable_concept(c.type_codings, c.type_text)
    if ctype:
        entry["type"] = ctype

    capacity = _fhir_simple_quantity(c, "capacity")
    if capacity:
        entry["capacity"] = capacity

    quantity = _fhir_simple_quantity(c, "specimen_quantity")
    if quantity:
        entry["specimenQuantity"] = quantity

    additive_concept = fhir_specimen_codeable_concept(
        c.additive_codings, c.additive_codeable_concept_text
    )
    if additive_concept:
        entry["additiveCodeableConcept"] = additive_concept

    additive_ref = _fhir_reference_with_identifier_fallback(c, "additive_reference")
    if additive_ref:
        entry["additiveReference"] = additive_ref

    return entry


def fhir_specimen_note(n) -> dict:
    entry: dict = {}
    if n.author_string:
        entry["authorString"] = n.author_string
    else:
        author_ref = _fhir_reference_with_identifier_fallback(n, "author")
        if author_ref:
            entry["authorReference"] = author_ref

    if n.time:
        entry["time"] = fhir_instant(n.time)
    if n.text:
        entry["text"] = n.text
    return entry


def to_fhir_specimen(specimen: SpecimenModel) -> dict:
    """Transform SpecimenModel to FHIR R4 Specimen resource dictionary."""
    result: dict = {
        "resourceType": "Specimen",
        "id": str(specimen.specimen_id),
    }

    if specimen.extension:
        result["extension"] = specimen.extension

    identifiers = [fhir_specimen_identifier(i) for i in (specimen.identifiers or [])]
    identifiers = [i for i in identifiers if i]
    if identifiers:
        result["identifier"] = identifiers

    accession = fhir_specimen_accession_identifier(specimen)
    if accession:
        result["accessionIdentifier"] = accession

    if specimen.status:
        result["status"] = fhir_enum(specimen.status)

    type_concept = fhir_specimen_codeable_concept(
        specimen.type_codings, specimen.type_text
    )
    if type_concept:
        result["type"] = type_concept

    subject = _fhir_reference_with_identifier_fallback(specimen, "subject")
    if subject:
        result["subject"] = subject

    if specimen.received_time:
        result["receivedTime"] = fhir_instant(specimen.received_time)

    parents = [
        _fhir_reference_with_identifier_fallback(p, "reference")
        for p in (specimen.parents or [])
    ]
    parents = [p for p in parents if p]
    if parents:
        result["parent"] = parents

    requests = [
        _fhir_reference_with_identifier_fallback(r, "reference")
        for r in (specimen.requests or [])
    ]
    requests = [r for r in requests if r]
    if requests:
        result["request"] = requests

    collection = fhir_specimen_collection(specimen)
    if collection:
        result["collection"] = collection

    processings = [
        fhir_specimen_processing(p) for p in (specimen.processings or [])
    ]
    processings = [p for p in processings if p]
    if processings:
        result["processing"] = processings

    containers = [fhir_specimen_container(c) for c in (specimen.containers or [])]
    containers = [c for c in containers if c]
    if containers:
        result["container"] = containers

    conditions = [
        fhir_specimen_codeable_concept(cond.codings, cond.text)
        for cond in (specimen.conditions or [])
    ]
    conditions = [c for c in conditions if c]
    if conditions:
        result["condition"] = conditions

    notes = [fhir_specimen_note(n) for n in (specimen.notes or [])]
    notes = [n for n in notes if n]
    if notes:
        result["note"] = notes

    return {k: v for k, v in result.items() if v is not None}
