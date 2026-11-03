from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.medication_administration import (
        MedicationAdministrationDevice,
        MedicationAdministrationEventHistory,
        MedicationAdministrationIdentifier,
        MedicationAdministrationModel,
        MedicationAdministrationNote,
        MedicationAdministrationPartOf,
        MedicationAdministrationPerformer,
        MedicationAdministrationReasonCode,
        MedicationAdministrationReasonReference,
        MedicationAdministrationStatusReason,
        MedicationAdministrationSupportingInformation,
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


def fhir_medication_administration_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _fhir_coding_list(codings)
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _fhir_reference_with_identifier_fallback(obj, prefix: str) -> dict:
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
            type_cc: dict = {}
            if id_type_text:
                type_cc["text"] = id_type_text
            type_coding: dict = {}
            if id_type_system:
                type_coding["system"] = id_type_system
            if id_type_version:
                type_coding["version"] = id_type_version
            if id_type_code:
                type_coding["code"] = id_type_code
            if id_type_display:
                type_coding["display"] = id_type_display
            if id_type_user_selected is not None:
                type_coding["userSelected"] = id_type_user_selected
            if type_coding:
                type_cc["coding"] = [type_coding]
            if type_cc:
                identifier["type"] = type_cc
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        if id_period_start or id_period_end:
            period: dict = {}
            if id_period_start:
                period["start"] = fhir_instant(id_period_start)
            if id_period_end:
                period["end"] = fhir_instant(id_period_end)
            if period:
                identifier["period"] = period
        if identifier:
            entry["identifier"] = identifier

    return entry


def fhir_medication_administration_identifier(i: MedicationAdministrationIdentifier) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    type_cc = fhir_medication_administration_codeable_concept(i.type_codings, i.type_text)
    if type_cc:
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    if i.period_start or i.period_end:
        p: dict = {}
        if i.period_start:
            p["start"] = fhir_instant(i.period_start)
        if i.period_end:
            p["end"] = fhir_instant(i.period_end)
        if p:
            entry["period"] = p

    assigner = _fhir_reference_with_identifier_fallback(i, "assigner")
    if assigner:
        entry["assigner"] = assigner

    return entry


def fhir_medication_administration_part_of(p: MedicationAdministrationPartOf) -> dict:
    return _fhir_reference_with_identifier_fallback(p, "reference")


def fhir_medication_administration_status_reason(sr: MedicationAdministrationStatusReason) -> dict:
    return fhir_medication_administration_codeable_concept(sr.codings, sr.text) or {}


def fhir_medication_administration_supporting_info(si: MedicationAdministrationSupportingInformation) -> dict:
    return _fhir_reference_with_identifier_fallback(si, "reference")


def fhir_medication_administration_performer(p: MedicationAdministrationPerformer) -> dict:
    entry: dict = {}
    func = fhir_medication_administration_codeable_concept(p.function_codings, p.function_text)
    if func:
        entry["function"] = func
    actor = _fhir_reference_with_identifier_fallback(p, "actor")
    if actor:
        entry["actor"] = actor
    return entry


def fhir_medication_administration_reason_code(rc: MedicationAdministrationReasonCode) -> dict:
    return fhir_medication_administration_codeable_concept(rc.codings, rc.text) or {}


def fhir_medication_administration_reason_reference(rr: MedicationAdministrationReasonReference) -> dict:
    return _fhir_reference_with_identifier_fallback(rr, "reference")


def fhir_medication_administration_device(d: MedicationAdministrationDevice) -> dict:
    return _fhir_reference_with_identifier_fallback(d, "reference")


def fhir_medication_administration_note(n: MedicationAdministrationNote) -> dict:
    entry: dict = {"text": n.text}
    if n.time:
        entry["time"] = fhir_instant(n.time)
    if n.author_string:
        entry["authorString"] = n.author_string
    else:
        author_ref = _fhir_reference_with_identifier_fallback(n, "author")
        if author_ref:
            entry["authorReference"] = author_ref
    return entry


def fhir_medication_administration_event_history(eh: MedicationAdministrationEventHistory) -> dict:
    return _fhir_reference_with_identifier_fallback(eh, "reference")


def fhir_medication_administration_dosage(model: MedicationAdministrationModel) -> dict | None:
    d: dict = {}
    if model.dosage_text:
        d["text"] = model.dosage_text
    if model.dosage_site_codings or model.dosage_site_text:
        site = fhir_medication_administration_codeable_concept(model.dosage_site_codings, model.dosage_site_text)
        if site:
            d["site"] = site
    if model.dosage_route_codings or model.dosage_route_text:
        route = fhir_medication_administration_codeable_concept(model.dosage_route_codings, model.dosage_route_text)
        if route:
            d["route"] = route
    if model.dosage_method_codings or model.dosage_method_text:
        method = fhir_medication_administration_codeable_concept(model.dosage_method_codings, model.dosage_method_text)
        if method:
            d["method"] = method
    if model.dosage_dose_value is not None:
        d["dose"] = {
            k: v
            for k, v in {
                "value": float(model.dosage_dose_value),
                "unit": model.dosage_dose_unit,
                "system": model.dosage_dose_system,
                "code": model.dosage_dose_code,
            }.items()
            if v is not None
        }
    if (
        model.dosage_rate_ratio_numerator_value is not None
        or model.dosage_rate_ratio_denominator_value is not None
    ):
        num = {
            k: v
            for k, v in {
                "value": float(model.dosage_rate_ratio_numerator_value)
                if model.dosage_rate_ratio_numerator_value is not None
                else None,
                "unit": model.dosage_rate_ratio_numerator_unit,
                "system": model.dosage_rate_ratio_numerator_system,
                "code": model.dosage_rate_ratio_numerator_code,
            }.items()
            if v is not None
        }
        den = {
            k: v
            for k, v in {
                "value": float(model.dosage_rate_ratio_denominator_value)
                if model.dosage_rate_ratio_denominator_value is not None
                else None,
                "unit": model.dosage_rate_ratio_denominator_unit,
                "system": model.dosage_rate_ratio_denominator_system,
                "code": model.dosage_rate_ratio_denominator_code,
            }.items()
            if v is not None
        }
        ratio = {}
        if num:
            ratio["numerator"] = num
        if den:
            ratio["denominator"] = den
        if ratio:
            d["rateRatio"] = ratio
    elif model.dosage_rate_quantity_value is not None:
        d["rateQuantity"] = {
            k: v
            for k, v in {
                "value": float(model.dosage_rate_quantity_value),
                "unit": model.dosage_rate_quantity_unit,
                "system": model.dosage_rate_quantity_system,
                "code": model.dosage_rate_quantity_code,
            }.items()
            if v is not None
        }
    return d or None


def _fhir_meta(model: MedicationAdministrationModel) -> dict:
    meta: dict = {}
    if model.updated_at:
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    return meta


def to_fhir_medication_administration(model: MedicationAdministrationModel) -> dict:
    res: dict = {
        "resourceType": "MedicationAdministration",
        "id": str(model.medication_administration_id),
        "status": fhir_enum(model.status),
    }

    meta = _fhir_meta(model)
    if meta:
        res["meta"] = meta

    if model.category_codings or model.category_text:
        cat = fhir_medication_administration_codeable_concept(model.category_codings, model.category_text)
        if cat:
            res["category"] = cat

    # medication[x] (1..1 choice)
    if model.medication_codings or model.medication_codeable_concept_text:
        med_cc = fhir_medication_administration_codeable_concept(
            model.medication_codings, model.medication_codeable_concept_text
        )
        if med_cc:
            res["medicationCodeableConcept"] = med_cc
    else:
        med_ref = _fhir_reference_with_identifier_fallback(model, "medication")
        if med_ref:
            res["medicationReference"] = med_ref

    # subject (1..1)
    subj = _fhir_reference_with_identifier_fallback(model, "subject")
    if subj:
        res["subject"] = subj

    # context
    ctx = _fhir_reference_with_identifier_fallback(model, "context")
    if ctx:
        res["context"] = ctx

    # effective[x] (1..1 choice: dateTime | Period)
    if model.effective_date_time:
        res["effectiveDateTime"] = fhir_instant(model.effective_date_time)
    elif model.effective_period_start or model.effective_period_end:
        res["effectivePeriod"] = {
            k: v
            for k, v in {
                "start": fhir_instant(model.effective_period_start) if model.effective_period_start else None,
                "end": fhir_instant(model.effective_period_end) if model.effective_period_end else None,
            }.items()
            if v is not None
        }

    # request
    req = _fhir_reference_with_identifier_fallback(model, "request")
    if req:
        res["request"] = req

    # instantiates
    if model.instantiates:
        res["instantiates"] = list(model.instantiates)

    # partOf
    po_list = [fhir_medication_administration_part_of(p) for p in (model.part_of or [])]
    po_list = [p for p in po_list if p]
    if po_list:
        res["partOf"] = po_list

    # statusReason
    sr_list = [fhir_medication_administration_status_reason(sr) for sr in (model.status_reasons or [])]
    sr_list = [sr for sr in sr_list if sr]
    if sr_list:
        res["statusReason"] = sr_list

    # supportingInformation
    si_list = [fhir_medication_administration_supporting_info(si) for si in (model.supporting_informations or [])]
    si_list = [si for si in si_list if si]
    if si_list:
        res["supportingInformation"] = si_list

    # performer
    perf_list = [fhir_medication_administration_performer(p) for p in (model.performers or [])]
    perf_list = [p for p in perf_list if p]
    if perf_list:
        res["performer"] = perf_list

    # reasonCode
    rc_list = [fhir_medication_administration_reason_code(rc) for rc in (model.reason_codes or [])]
    rc_list = [rc for rc in rc_list if rc]
    if rc_list:
        res["reasonCode"] = rc_list

    # reasonReference
    rr_list = [fhir_medication_administration_reason_reference(rr) for rr in (model.reason_references or [])]
    rr_list = [rr for rr in rr_list if rr]
    if rr_list:
        res["reasonReference"] = rr_list

    # device
    dev_list = [fhir_medication_administration_device(d) for d in (model.devices or [])]
    dev_list = [d for d in dev_list if d]
    if dev_list:
        res["device"] = dev_list

    # note
    notes = [fhir_medication_administration_note(n) for n in (model.notes or [])]
    notes = [n for n in notes if n]
    if notes:
        res["note"] = notes

    # dosage
    dosage = fhir_medication_administration_dosage(model)
    if dosage:
        res["dosage"] = dosage

    # eventHistory
    eh_list = [fhir_medication_administration_event_history(eh) for eh in (model.event_history or [])]
    eh_list = [eh for eh in eh_list if eh]
    if eh_list:
        res["eventHistory"] = eh_list

    # identifier
    identifiers = [fhir_medication_administration_identifier(i) for i in (model.identifiers or [])]
    identifiers = [i for i in identifiers if i]
    if identifiers:
        res["identifier"] = identifiers

    if model.extension:
        res["extension"] = list(model.extension)

    return {k: v for k, v in res.items() if v is not None}
