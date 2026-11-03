from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.medication_dispense import (
        MedicationDispenseAuthorizingPrescription,
        MedicationDispenseDetectedIssue,
        MedicationDispenseDosageInstruction,
        MedicationDispenseEventHistory,
        MedicationDispenseIdentifier,
        MedicationDispenseModel,
        MedicationDispenseNote,
        MedicationDispensePartOf,
        MedicationDispensePerformer,
        MedicationDispenseReceiver,
        MedicationDispenseSupportingInfo,
    )


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


def fhir_medication_dispense_codeable_concept(codings, text: str | None) -> dict | None:
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
    id_type_system = getattr(obj, f"{prefix}_identifier_type_system", None)
    id_type_version = getattr(obj, f"{prefix}_identifier_type_version", None)
    id_type_code = getattr(obj, f"{prefix}_identifier_type_code", None)
    id_type_display = getattr(obj, f"{prefix}_identifier_type_display", None)
    id_type_user_selected = getattr(obj, f"{prefix}_identifier_type_user_selected", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)

    if (
        id_use
        or id_type_system
        or id_type_version
        or id_type_code
        or id_type_display
        or id_type_user_selected
        or id_type_text
        or id_system
        or id_value
        or id_period_start
        or id_period_end
    ):
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
        if (
            id_type_system
            or id_type_code
            or id_type_text
            or id_type_display
            or id_type_version
            or id_type_user_selected
        ):
            type_coding: dict = {}
            if id_type_system:
                type_coding["system"] = id_type_system
            if id_type_code:
                type_coding["code"] = id_type_code
            if id_type_display:
                type_coding["display"] = id_type_display
            if id_type_version:
                type_coding["version"] = id_type_version
            if id_type_user_selected is not None:
                type_coding["userSelected"] = id_type_user_selected
            t: dict = {}
            if type_coding:
                t["coding"] = [type_coding]
            if id_type_text:
                t["text"] = id_type_text
            if t:
                identifier["type"] = t
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        period: dict = {}
        if id_period_start:
            period["start"] = fhir_instant(id_period_start)
        if id_period_end:
            period["end"] = fhir_instant(id_period_end)
        if period:
            identifier["period"] = period
        if identifier:
            entry["identifier"] = identifier

    return entry or None


def _fhir_reference_from_child(child) -> dict | None:
    return _fhir_reference_with_identifier_fallback(child, "reference")


def _fhir_identifier(i: MedicationDispenseIdentifier) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    type_cc = fhir_medication_dispense_codeable_concept(i.type_codings, i.type_text)
    if type_cc:
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    period: dict = {}
    if i.period_start:
        period["start"] = fhir_instant(i.period_start)
    if i.period_end:
        period["end"] = fhir_instant(i.period_end)
    if period:
        entry["period"] = period
    assigner = _fhir_reference_with_identifier_fallback(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def _fhir_quantity(obj, prefix: str) -> dict | None:
    val = getattr(obj, f"{prefix}_value", None)
    unit = getattr(obj, f"{prefix}_unit", None)
    system = getattr(obj, f"{prefix}_system", None)
    code = getattr(obj, f"{prefix}_code", None)
    if val is None and not unit and not system and not code:
        return None
    res: dict = {}
    if val is not None:
        res["value"] = float(val)
    if unit:
        res["unit"] = unit
    if system:
        res["system"] = system
    if code:
        res["code"] = code
    return res


def _fhir_performer(p: MedicationDispensePerformer) -> dict:
    entry: dict = {}
    func = fhir_medication_dispense_codeable_concept(p.function_codings, p.function_text)
    if func:
        entry["function"] = func
    actor = _fhir_reference_with_identifier_fallback(p, "actor")
    if actor:
        entry["actor"] = actor
    return entry


def _fhir_note(n: MedicationDispenseNote) -> dict:
    entry: dict = {}
    author_ref = _fhir_reference_with_identifier_fallback(n, "author")
    if author_ref:
        entry["authorReference"] = author_ref
    elif n.author_string:
        entry["authorString"] = n.author_string
    if n.time:
        entry["time"] = fhir_instant(n.time)
    if n.text:
        entry["text"] = n.text
    return entry


def _fhir_dosage(d: MedicationDispenseDosageInstruction) -> dict:
    entry: dict = {}
    if d.sequence is not None:
        entry["sequence"] = d.sequence
    if d.text:
        entry["text"] = d.text
    additional_instructions = [
        fhir_medication_dispense_codeable_concept(ai.codings, ai.text)
        for ai in (d.additional_instructions or [])
    ]
    additional_instructions = [ai for ai in additional_instructions if ai]
    if additional_instructions:
        entry["additionalInstruction"] = additional_instructions
    if d.patient_instruction:
        entry["patientInstruction"] = d.patient_instruction
    if d.timing:
        entry["timing"] = dict(d.timing)

    if d.as_needed_boolean is not None:
        entry["asNeededBoolean"] = d.as_needed_boolean
    else:
        as_needed_cc = fhir_medication_dispense_codeable_concept(
            d.as_needed_codings, d.as_needed_codeable_concept_text
        )
        if as_needed_cc:
            entry["asNeededCodeableConcept"] = as_needed_cc

    site = fhir_medication_dispense_codeable_concept(d.site_codings, d.site_text)
    if site:
        entry["site"] = site
    route = fhir_medication_dispense_codeable_concept(d.route_codings, d.route_text)
    if route:
        entry["route"] = route
    method = fhir_medication_dispense_codeable_concept(d.method_codings, d.method_text)
    if method:
        entry["method"] = method

    if d.dose_and_rate:
        entry["doseAndRate"] = list(d.dose_and_rate)
    if d.max_dose_per_period:
        entry["maxDosePerPeriod"] = dict(d.max_dose_per_period)

    max_dose_admin = _fhir_quantity(d, "max_dose_per_administration")
    if max_dose_admin:
        entry["maxDosePerAdministration"] = max_dose_admin
    max_dose_life = _fhir_quantity(d, "max_dose_per_lifetime")
    if max_dose_life:
        entry["maxDosePerLifetime"] = max_dose_life

    return entry


def _fhir_substitution(md: MedicationDispenseModel) -> dict | None:
    has_sub = (
        md.substitution_was_substituted is not None
        or md.substitution_type_text
        or md.substitution_type_codings
        or md.substitution_reasons
        or md.substitution_responsible_parties
    )
    if not has_sub:
        return None

    entry: dict = {
        "wasSubstituted": bool(md.substitution_was_substituted)
        if md.substitution_was_substituted is not None
        else False
    }
    type_cc = fhir_medication_dispense_codeable_concept(
        md.substitution_type_codings, md.substitution_type_text
    )
    if type_cc:
        entry["type"] = type_cc

    reasons = [
        fhir_medication_dispense_codeable_concept(r.codings, r.text)
        for r in (md.substitution_reasons or [])
    ]
    reasons = [r for r in reasons if r]
    if reasons:
        entry["reason"] = reasons

    parties = [
        _fhir_reference_from_child(rp)
        for rp in (md.substitution_responsible_parties or [])
    ]
    parties = [p for p in parties if p]
    if parties:
        entry["responsibleParty"] = parties

    return entry


_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


def _fhir_meta(md: MedicationDispenseModel) -> dict:
    meta: dict = {}
    if md.updated_at:
        meta["lastUpdated"] = fhir_instant(md.updated_at)
    extensions = []
    if md.tenant_id:
        extensions.append({"url": f"{_EXT_BASE}/org-id", "valueString": md.tenant_id})
    if md.created_by:
        extensions.append({"url": f"{_EXT_BASE}/created-by", "valueString": md.created_by})
    if md.updated_by:
        extensions.append({"url": f"{_EXT_BASE}/updated-by", "valueString": md.updated_by})
    if md.created_at:
        extensions.append({"url": f"{_EXT_BASE}/created-at", "valueDateTime": fhir_instant(md.created_at)})
    if extensions:
        meta["extension"] = extensions
    return meta


def to_fhir_medication_dispense(md: MedicationDispenseModel) -> dict:
    """Format a MedicationDispenseModel as a FHIR R4 JSON dict."""
    out: dict = {
        "resourceType": "MedicationDispense",
        "id": str(md.medication_dispense_id),
    }

    meta = _fhir_meta(md)
    if meta:
        out["meta"] = meta

    if md.extension:
        out["extension"] = list(md.extension)

    identifiers = [_fhir_identifier(i) for i in (md.identifiers or [])]
    if identifiers:
        out["identifier"] = identifiers

    part_of = [_fhir_reference_from_child(p) for p in (md.part_of or [])]
    part_of = [p for p in part_of if p]
    if part_of:
        out["partOf"] = part_of

    out["status"] = fhir_enum(md.status)

    status_reason_cc = fhir_medication_dispense_codeable_concept(
        md.status_reason_codings, md.status_reason_codeable_concept_text
    )
    if status_reason_cc:
        out["statusReasonCodeableConcept"] = status_reason_cc
    status_reason_ref = _fhir_reference_with_identifier_fallback(
        md, "status_reason_reference"
    )
    if status_reason_ref:
        out["statusReasonReference"] = status_reason_ref

    category = fhir_medication_dispense_codeable_concept(
        md.category_codings, md.category_text
    )
    if category:
        out["category"] = category

    medication_cc = fhir_medication_dispense_codeable_concept(
        md.medication_codings, md.medication_codeable_concept_text
    )
    if medication_cc:
        out["medicationCodeableConcept"] = medication_cc
    medication_ref = _fhir_reference_with_identifier_fallback(md, "medication")
    if medication_ref:
        out["medicationReference"] = medication_ref

    subject = _fhir_reference_with_identifier_fallback(md, "subject")
    if subject:
        out["subject"] = subject

    context = _fhir_reference_with_identifier_fallback(md, "context")
    if context:
        out["context"] = context

    supporting_infos = [
        _fhir_reference_from_child(s) for s in (md.supporting_informations or [])
    ]
    supporting_infos = [s for s in supporting_infos if s]
    if supporting_infos:
        out["supportingInformation"] = supporting_infos

    performers = [_fhir_performer(p) for p in (md.performers or [])]
    if performers:
        out["performer"] = performers

    location = _fhir_reference_with_identifier_fallback(md, "location")
    if location:
        out["location"] = location

    authorizing_prescriptions = [
        _fhir_reference_from_child(a) for a in (md.authorizing_prescriptions or [])
    ]
    authorizing_prescriptions = [a for a in authorizing_prescriptions if a]
    if authorizing_prescriptions:
        out["authorizingPrescription"] = authorizing_prescriptions

    dispense_type = fhir_medication_dispense_codeable_concept(
        md.type_codings, md.type_text
    )
    if dispense_type:
        out["type"] = dispense_type

    quantity = _fhir_quantity(md, "quantity")
    if quantity:
        out["quantity"] = quantity

    days_supply = _fhir_quantity(md, "days_supply")
    if days_supply:
        out["daysSupply"] = days_supply

    if md.when_prepared:
        out["whenPrepared"] = fhir_instant(md.when_prepared)

    if md.when_handed_over:
        out["whenHandedOver"] = fhir_instant(md.when_handed_over)

    destination = _fhir_reference_with_identifier_fallback(md, "destination")
    if destination:
        out["destination"] = destination

    receivers = [_fhir_reference_from_child(r) for r in (md.receivers or [])]
    receivers = [r for r in receivers if r]
    if receivers:
        out["receiver"] = receivers

    notes = [_fhir_note(n) for n in (md.notes or [])]
    if notes:
        out["note"] = notes

    dosages = [_fhir_dosage(d) for d in (md.dosage_instructions or [])]
    if dosages:
        out["dosageInstruction"] = dosages

    substitution = _fhir_substitution(md)
    if substitution:
        out["substitution"] = substitution

    detected_issues = [
        _fhir_reference_from_child(d) for d in (md.detected_issues or [])
    ]
    detected_issues = [d for d in detected_issues if d]
    if detected_issues:
        out["detectedIssue"] = detected_issues

    event_history = [_fhir_reference_from_child(e) for e in (md.event_history or [])]
    event_history = [e for e in event_history if e]
    if event_history:
        out["eventHistory"] = event_history

    return {k: v for k, v in out.items() if v is not None}
