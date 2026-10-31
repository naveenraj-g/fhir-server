"""Payload -> FHIR JSON conversion for Specimen.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(SpecimenCreateSchema / SpecimenPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.schemas.specimen.input import (
        SpecimenCodeableConceptInput,
        SpecimenCollectionInput,
        SpecimenContainerInput,
        SpecimenCreateSchema,
        SpecimenIdentifierInput,
        SpecimenNoteInput,
        SpecimenPatchSchema,
        SpecimenProcessingInput,
    )

_COMPARATOR_SYMBOLS = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}


def _coding_from_payload(c) -> dict:
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


def _codeable_concept_from_payload(concept: SpecimenCodeableConceptInput | None) -> dict | None:
    if not concept:
        return None
    codings = [_coding_from_payload(c) for c in (concept.coding or [])]
    codings = [c for c in codings if c]
    result: dict = {}
    if codings:
        result["coding"] = codings
    if concept.text:
        result["text"] = concept.text
    return result or None


def _reference_from_payload(ref) -> dict | None:
    if not ref:
        return None
    raw_reference = getattr(ref, "reference", None)
    display = getattr(ref, "reference_display", None)

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    if display:
        entry["display"] = display

    id_use = getattr(ref, "reference_identifier_use", None)
    id_system = getattr(ref, "reference_identifier_system", None)
    id_value = getattr(ref, "reference_identifier_value", None)
    id_type_text = getattr(ref, "reference_identifier_type_text", None)

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


def _identifier_from_payload(i: SpecimenIdentifierInput) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value

    type_codings = [_coding_from_payload(c) for c in (i.type_coding or [])]
    type_codings = [c for c in type_codings if c]
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
            p["start"] = i.period_start.isoformat()
        if i.period_end:
            p["end"] = i.period_end.isoformat()
        entry["period"] = p

    if i.assigner or i.assigner_display or i.assigner_identifier_system or i.assigner_identifier_value:
        assigner: dict = {}
        if i.assigner:
            assigner["reference"] = i.assigner
        if i.assigner_display:
            assigner["display"] = i.assigner_display
        if i.assigner_identifier_system or i.assigner_identifier_value:
            ident: dict = {}
            if i.assigner_identifier_use:
                ident["use"] = fhir_enum(i.assigner_identifier_use)
            if i.assigner_identifier_system:
                ident["system"] = i.assigner_identifier_system
            if i.assigner_identifier_value:
                ident["value"] = i.assigner_identifier_value
            if i.assigner_identifier_type_text:
                ident["type"] = {"text": i.assigner_identifier_type_text}
            assigner["identifier"] = ident
        entry["assigner"] = assigner

    return entry


def _collection_from_payload(col: SpecimenCollectionInput) -> dict | None:
    entry: dict = {}

    collector = _reference_from_payload(col.collector)
    if collector:
        entry["collector"] = collector

    if col.collected_date_time:
        entry["collectedDateTime"] = col.collected_date_time.isoformat()
    elif col.collected_period_start or col.collected_period_end:
        p: dict = {}
        if col.collected_period_start:
            p["start"] = col.collected_period_start.isoformat()
        if col.collected_period_end:
            p["end"] = col.collected_period_end.isoformat()
        entry["collectedPeriod"] = p

    if col.duration_value is not None:
        comparator = getattr(col, "duration_comparator", None)
        entry["duration"] = {
            k: v
            for k, v in {
                "value": col.duration_value,
                "comparator": _COMPARATOR_SYMBOLS.get(fhir_enum(comparator), fhir_enum(comparator)) if comparator else None,
                "unit": col.duration_unit,
                "system": col.duration_system,
                "code": col.duration_code,
            }.items()
            if v is not None
        }

    if col.quantity_value is not None:
        entry["quantity"] = {
            k: v
            for k, v in {
                "value": col.quantity_value,
                "unit": col.quantity_unit,
                "system": col.quantity_system,
                "code": col.quantity_code,
            }.items()
            if v is not None
        }

    method = _codeable_concept_from_payload(col.method)
    if method:
        entry["method"] = method

    body_site = _codeable_concept_from_payload(col.body_site)
    if body_site:
        entry["bodySite"] = body_site

    fasting_concept = _codeable_concept_from_payload(col.fasting_status_codeable_concept)
    if fasting_concept:
        entry["fastingStatusCodeableConcept"] = fasting_concept
    elif col.fasting_status_duration_value is not None:
        f_comp = getattr(col, "fasting_status_duration_comparator", None)
        entry["fastingStatusDuration"] = {
            k: v
            for k, v in {
                "value": col.fasting_status_duration_value,
                "comparator": _COMPARATOR_SYMBOLS.get(fhir_enum(f_comp), fhir_enum(f_comp)) if f_comp else None,
                "unit": col.fasting_status_duration_unit,
                "system": col.fasting_status_duration_system,
                "code": col.fasting_status_duration_code,
            }.items()
            if v is not None
        }

    return entry or None


def _processing_from_payload(p: SpecimenProcessingInput) -> dict:
    entry: dict = {}
    if p.description:
        entry["description"] = p.description

    procedure = _codeable_concept_from_payload(p.procedure)
    if procedure:
        entry["procedure"] = procedure

    additives = [_reference_from_payload(a) for a in (p.additive or [])]
    additives = [a for a in additives if a]
    if additives:
        entry["additive"] = additives

    if p.time_date_time:
        entry["timeDateTime"] = p.time_date_time.isoformat()
    elif p.time_period_start or p.time_period_end:
        period: dict = {}
        if p.time_period_start:
            period["start"] = p.time_period_start.isoformat()
        if p.time_period_end:
            period["end"] = p.time_period_end.isoformat()
        entry["timePeriod"] = period

    return entry


def _container_from_payload(c: SpecimenContainerInput) -> dict:
    entry: dict = {}

    identifiers = [_identifier_from_payload(i) for i in (c.identifier or [])]
    identifiers = [i for i in identifiers if i]
    if identifiers:
        entry["identifier"] = identifiers

    if c.description:
        entry["description"] = c.description

    ctype = _codeable_concept_from_payload(c.type)
    if ctype:
        entry["type"] = ctype

    if c.capacity_value is not None:
        entry["capacity"] = {
            k: v
            for k, v in {
                "value": c.capacity_value,
                "unit": c.capacity_unit,
                "system": c.capacity_system,
                "code": c.capacity_code,
            }.items()
            if v is not None
        }

    if c.specimen_quantity_value is not None:
        entry["specimenQuantity"] = {
            k: v
            for k, v in {
                "value": c.specimen_quantity_value,
                "unit": c.specimen_quantity_unit,
                "system": c.specimen_quantity_system,
                "code": c.specimen_quantity_code,
            }.items()
            if v is not None
        }

    additive_concept = _codeable_concept_from_payload(c.additive_codeable_concept)
    if additive_concept:
        entry["additiveCodeableConcept"] = additive_concept

    additive_ref = _reference_from_payload(c.additive_reference)
    if additive_ref:
        entry["additiveReference"] = additive_ref

    return entry


def _note_from_payload(n: SpecimenNoteInput) -> dict:
    entry: dict = {}
    if n.author_string:
        entry["authorString"] = n.author_string
    elif n.author_reference or n.author_display:
        author_ref: dict = {}
        if n.author_reference:
            author_ref["reference"] = n.author_reference
        if n.author_display:
            author_ref["display"] = n.author_display
        if n.author_identifier_system or n.author_identifier_value:
            ident: dict = {}
            if n.author_identifier_use:
                ident["use"] = fhir_enum(n.author_identifier_use)
            if n.author_identifier_system:
                ident["system"] = n.author_identifier_system
            if n.author_identifier_value:
                ident["value"] = n.author_identifier_value
            if n.author_identifier_type_text:
                ident["type"] = {"text": n.author_identifier_type_text}
            author_ref["identifier"] = ident
        entry["authorReference"] = author_ref

    if n.time:
        entry["time"] = n.time.isoformat()
    if n.text:
        entry["text"] = n.text
    return entry


def payload_to_fhir_specimen(payload: SpecimenCreateSchema) -> dict:
    """Build a complete FHIR R4 Specimen dict from a create payload."""
    result: dict = {
        "resourceType": "Specimen",
    }

    if payload.extension:
        result["extension"] = payload.extension

    if payload.identifier:
        identifiers = [_identifier_from_payload(i) for i in payload.identifier]
        identifiers = [i for i in identifiers if i]
        if identifiers:
            result["identifier"] = identifiers

    if payload.accession_identifier:
        accession = _identifier_from_payload(payload.accession_identifier)
        if accession:
            result["accessionIdentifier"] = accession

    if payload.status:
        result["status"] = fhir_enum(payload.status)

    type_concept = _codeable_concept_from_payload(payload.type)
    if type_concept:
        result["type"] = type_concept

    subject = _reference_from_payload(payload.subject)
    if subject:
        result["subject"] = subject

    if payload.received_time:
        result["receivedTime"] = payload.received_time.isoformat()

    if payload.parent:
        parents = [_reference_from_payload(p) for p in payload.parent]
        parents = [p for p in parents if p]
        if parents:
            result["parent"] = parents

    if payload.request:
        requests = [_reference_from_payload(r) for r in payload.request]
        requests = [r for r in requests if r]
        if requests:
            result["request"] = requests

    if payload.collection:
        collection = _collection_from_payload(payload.collection)
        if collection:
            result["collection"] = collection

    if payload.processing:
        processings = [_processing_from_payload(p) for p in payload.processing]
        processings = [p for p in processings if p]
        if processings:
            result["processing"] = processings

    if payload.container:
        containers = [_container_from_payload(c) for c in payload.container]
        containers = [c for c in containers if c]
        if containers:
            result["container"] = containers

    if payload.condition:
        conditions = [_codeable_concept_from_payload(c) for c in payload.condition]
        conditions = [c for c in conditions if c]
        if conditions:
            result["condition"] = conditions

    if payload.note:
        notes = [_note_from_payload(n) for n in payload.note]
        notes = [n for n in notes if n]
        if notes:
            result["note"] = notes

    return result


def patch_fragment_to_fhir_specimen(payload: SpecimenPatchSchema) -> tuple[dict, set[str]]:
    """Build a partial FHIR R4 Specimen dict and a set of touched FHIR keys from a patch payload."""
    provided = payload.model_dump(exclude_unset=True)
    fragment: dict = {}
    touched: set[str] = set()

    if "extension" in provided:
        touched.add("extension")
        if payload.extension:
            fragment["extension"] = payload.extension

    if "identifier" in provided:
        touched.add("identifier")
        if payload.identifier:
            identifiers = [_identifier_from_payload(i) for i in payload.identifier]
            identifiers = [i for i in identifiers if i]
            if identifiers:
                fragment["identifier"] = identifiers

    if "accession_identifier" in provided:
        touched.add("accessionIdentifier")
        if payload.accession_identifier:
            accession = _identifier_from_payload(payload.accession_identifier)
            if accession:
                fragment["accessionIdentifier"] = accession

    if "status" in provided:
        touched.add("status")
        if payload.status:
            fragment["status"] = fhir_enum(payload.status)

    if "type" in provided:
        touched.add("type")
        if payload.type:
            type_concept = _codeable_concept_from_payload(payload.type)
            if type_concept:
                fragment["type"] = type_concept

    if "subject" in provided:
        touched.add("subject")
        if payload.subject:
            subject = _reference_from_payload(payload.subject)
            if subject:
                fragment["subject"] = subject

    if "received_time" in provided:
        touched.add("receivedTime")
        if payload.received_time:
            fragment["receivedTime"] = payload.received_time.isoformat()

    if "parent" in provided:
        touched.add("parent")
        if payload.parent:
            parents = [_reference_from_payload(p) for p in payload.parent]
            parents = [p for p in parents if p]
            if parents:
                fragment["parent"] = parents

    if "request" in provided:
        touched.add("request")
        if payload.request:
            requests = [_reference_from_payload(r) for r in payload.request]
            requests = [r for r in requests if r]
            if requests:
                fragment["request"] = requests

    if "collection" in provided:
        touched.add("collection")
        if payload.collection:
            collection = _collection_from_payload(payload.collection)
            if collection:
                fragment["collection"] = collection

    if "processing" in provided:
        touched.add("processing")
        if payload.processing:
            processings = [_processing_from_payload(p) for p in payload.processing]
            processings = [p for p in processings if p]
            if processings:
                fragment["processing"] = processings

    if "container" in provided:
        touched.add("container")
        if payload.container:
            containers = [_container_from_payload(c) for c in payload.container]
            containers = [c for c in containers if c]
            if containers:
                fragment["container"] = containers

    if "condition" in provided:
        touched.add("condition")
        if payload.condition:
            conditions = [_codeable_concept_from_payload(c) for c in payload.condition]
            conditions = [c for c in conditions if c]
            if conditions:
                fragment["condition"] = conditions

    if "note" in provided:
        touched.add("note")
        if payload.note:
            notes = [_note_from_payload(n) for n in payload.note]
            notes = [n for n in notes if n]
            if notes:
                fragment["note"] = notes

    return fragment, touched
