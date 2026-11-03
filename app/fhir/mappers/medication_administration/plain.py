from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

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


def _plain_coding_list(codings) -> list[dict]:
    result = []
    for c in codings or []:
        entry = {
            k: v
            for k, v in {
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "user_selected": c.user_selected,
            }.items()
            if v is not None
        }
        if entry:
            result.append(entry)
    return result


def plain_medication_administration_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _plain_coding_list(codings)
    result: dict = {}
    if text:
        result["text"] = text
    if coding_list:
        result["coding"] = coding_list
    return result or None


def _plain_reference(obj, prefix: str) -> dict:
    raw_reference = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    res: dict = {
        "reference": raw_reference,
        "type": fhir_enum(ref_type) if ref_type else None,
        "id": ref_id,
        "display": display,
    }

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    if id_use is not None:
        res["identifier_use"] = fhir_enum(id_use)
    for col in (
        "identifier_type_system",
        "identifier_type_version",
        "identifier_type_code",
        "identifier_type_display",
        "identifier_type_user_selected",
        "identifier_type_text",
        "identifier_system",
        "identifier_value",
        "identifier_period_start",
        "identifier_period_end",
    ):
        v = getattr(obj, f"{prefix}_{col}", None)
        if v is not None:
            res[col] = v

    return {k: v for k, v in res.items() if v is not None}


def plain_medication_administration_identifier(i: MedicationAdministrationIdentifier) -> dict:
    entry: dict = {
        "id": i.id,
        "use": fhir_enum(i.use) if i.use else None,
        "type": plain_medication_administration_codeable_concept(i.type_codings, i.type_text),
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start,
        "period_end": i.period_end,
    }
    assigner = _plain_reference(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return {k: v for k, v in entry.items() if v is not None}


def plain_medication_administration_part_of(p: MedicationAdministrationPartOf) -> dict:
    entry = _plain_reference(p, "reference")
    entry["id"] = p.id
    return entry


def plain_medication_administration_status_reason(sr: MedicationAdministrationStatusReason) -> dict:
    entry = plain_medication_administration_codeable_concept(sr.codings, sr.text) or {}
    entry["id"] = sr.id
    return entry


def plain_medication_administration_supporting_info(si: MedicationAdministrationSupportingInformation) -> dict:
    entry = _plain_reference(si, "reference")
    entry["id"] = si.id
    return entry


def plain_medication_administration_performer(p: MedicationAdministrationPerformer) -> dict:
    entry: dict = {
        "id": p.id,
        "actor": _plain_reference(p, "actor"),
    }
    func = plain_medication_administration_codeable_concept(p.function_codings, p.function_text)
    if func:
        entry["function"] = func
    return entry


def plain_medication_administration_reason_code(rc: MedicationAdministrationReasonCode) -> dict:
    entry = plain_medication_administration_codeable_concept(rc.codings, rc.text) or {}
    entry["id"] = rc.id
    return entry


def plain_medication_administration_reason_reference(rr: MedicationAdministrationReasonReference) -> dict:
    entry = _plain_reference(rr, "reference")
    entry["id"] = rr.id
    return entry


def plain_medication_administration_device(d: MedicationAdministrationDevice) -> dict:
    entry = _plain_reference(d, "reference")
    entry["id"] = d.id
    return entry


def plain_medication_administration_note(n: MedicationAdministrationNote) -> dict:
    entry: dict = {
        "id": n.id,
        "text": n.text,
        "time": n.time,
        "author_string": n.author_string,
    }
    author_ref = _plain_reference(n, "author")
    if author_ref:
        entry["author_reference"] = author_ref
    return {k: v for k, v in entry.items() if v is not None}


def plain_medication_administration_event_history(eh: MedicationAdministrationEventHistory) -> dict:
    entry = _plain_reference(eh, "reference")
    entry["id"] = eh.id
    return entry


def plain_medication_administration_dosage(model: MedicationAdministrationModel) -> dict | None:
    d: dict = {}
    if model.dosage_text:
        d["text"] = model.dosage_text
    if model.dosage_site_codings or model.dosage_site_text:
        site = plain_medication_administration_codeable_concept(model.dosage_site_codings, model.dosage_site_text)
        if site:
            d["site"] = site
    if model.dosage_route_codings or model.dosage_route_text:
        route = plain_medication_administration_codeable_concept(model.dosage_route_codings, model.dosage_route_text)
        if route:
            d["route"] = route
    if model.dosage_method_codings or model.dosage_method_text:
        method = plain_medication_administration_codeable_concept(model.dosage_method_codings, model.dosage_method_text)
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
            d["rate_ratio"] = ratio
    elif model.dosage_rate_quantity_value is not None:
        d["rate_quantity"] = {
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


def to_plain_medication_administration(model: MedicationAdministrationModel) -> dict:
    res: dict = {
        "id": model.medication_administration_id,
        "status": fhir_enum(model.status),
        "effective_date_time": model.effective_date_time,
        "effective_period_start": model.effective_period_start,
        "effective_period_end": model.effective_period_end,
    }

    if model.category_codings or model.category_text:
        cat = plain_medication_administration_codeable_concept(model.category_codings, model.category_text)
        if cat:
            res["category"] = cat

    # medication[x]
    if model.medication_codings or model.medication_codeable_concept_text:
        med_cc = plain_medication_administration_codeable_concept(
            model.medication_codings, model.medication_codeable_concept_text
        )
        if med_cc:
            res["medication_codeable_concept"] = med_cc
    else:
        med_ref = _plain_reference(model, "medication")
        if med_ref:
            res["medication_reference"] = med_ref

    # subject
    subj = _plain_reference(model, "subject")
    if subj:
        res["subject"] = subj

    # context
    ctx = _plain_reference(model, "context")
    if ctx:
        res["context"] = ctx

    # request
    req = _plain_reference(model, "request")
    if req:
        res["request"] = req

    # instantiates
    if model.instantiates:
        res["instantiates"] = list(model.instantiates)

    # part_of
    po_list = [plain_medication_administration_part_of(p) for p in (model.part_of or [])]
    if po_list:
        res["part_of"] = po_list

    # status_reason
    sr_list = [plain_medication_administration_status_reason(sr) for sr in (model.status_reasons or [])]
    if sr_list:
        res["status_reason"] = sr_list

    # supporting_information
    si_list = [plain_medication_administration_supporting_info(si) for si in (model.supporting_informations or [])]
    if si_list:
        res["supporting_information"] = si_list

    # performer
    perf_list = [plain_medication_administration_performer(p) for p in (model.performers or [])]
    if perf_list:
        res["performer"] = perf_list

    # reason_code
    rc_list = [plain_medication_administration_reason_code(rc) for rc in (model.reason_codes or [])]
    if rc_list:
        res["reason_code"] = rc_list

    # reason_reference
    rr_list = [plain_medication_administration_reason_reference(rr) for rr in (model.reason_references or [])]
    if rr_list:
        res["reason_reference"] = rr_list

    # device
    dev_list = [plain_medication_administration_device(d) for d in (model.devices or [])]
    if dev_list:
        res["device"] = dev_list

    # note
    notes = [plain_medication_administration_note(n) for n in (model.notes or [])]
    if notes:
        res["note"] = notes

    # dosage
    dosage = plain_medication_administration_dosage(model)
    if dosage:
        res["dosage"] = dosage

    # event_history
    eh_list = [plain_medication_administration_event_history(eh) for eh in (model.event_history or [])]
    if eh_list:
        res["event_history"] = eh_list

    # identifier
    identifiers = [plain_medication_administration_identifier(i) for i in (model.identifiers or [])]
    if identifiers:
        res["identifier"] = identifiers

    if model.extension:
        res["extension"] = list(model.extension)

    return {k: v for k, v in res.items() if v is not None}
