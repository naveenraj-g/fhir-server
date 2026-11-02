from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.medication_statement import (
        MedicationStatementDosage,
        MedicationStatementIdentifier,
        MedicationStatementModel,
        MedicationStatementNote,
        MedicationStatementReasonCode,
        MedicationStatementStatusReason,
    )

_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"
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


def fhir_medication_statement_codeable_concept(codings, text: str | None) -> dict | None:
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
            if id_type_system or id_type_code or id_type_display or id_type_version or id_type_user_selected:
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
                    "start": fhir_instant(id_period_start) if id_period_start else None,
                    "end": fhir_instant(id_period_end) if id_period_end else None,
                }.items()
                if v is not None
            }
        if identifier:
            entry["identifier"] = identifier

    return entry


def fhir_medication_statement_identifier(ident: MedicationStatementIdentifier) -> dict:
    res: dict = {}
    if ident.use:
        res["use"] = fhir_enum(ident.use)
    if ident.type_codings or ident.type_text:
        res["type"] = fhir_medication_statement_codeable_concept(ident.type_codings, ident.type_text)
    if ident.system:
        res["system"] = ident.system
    if ident.value:
        res["value"] = ident.value
    if ident.period_start or ident.period_end:
        res["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(ident.period_start) if ident.period_start else None,
                "end": fhir_instant(ident.period_end) if ident.period_end else None,
            }.items()
            if v is not None
        }
    assigner = _fhir_reference_with_identifier_fallback(ident, "assigner")
    if assigner:
        res["assigner"] = assigner
    return {k: v for k, v in res.items() if v is not None}


def fhir_medication_statement_based_on(bo) -> dict:
    return _fhir_reference_with_identifier_fallback(bo, "reference")


def fhir_medication_statement_part_of(po) -> dict:
    return _fhir_reference_with_identifier_fallback(po, "reference")


def fhir_medication_statement_derived_from(df) -> dict:
    return _fhir_reference_with_identifier_fallback(df, "reference")


def fhir_medication_statement_reason_reference(rr) -> dict:
    return _fhir_reference_with_identifier_fallback(rr, "reference")


def fhir_medication_statement_status_reason(sr: MedicationStatementStatusReason) -> dict | None:
    return fhir_medication_statement_codeable_concept(sr.codings, sr.text)


def fhir_medication_statement_reason_code(rc: MedicationStatementReasonCode) -> dict | None:
    return fhir_medication_statement_codeable_concept(rc.codings, rc.text)


def fhir_medication_statement_note(note: MedicationStatementNote) -> dict:
    res: dict = {"text": note.text}
    if note.time:
        res["time"] = fhir_instant(note.time)
    if note.author_string:
        res["authorString"] = note.author_string
    else:
        author_ref = _fhir_reference_with_identifier_fallback(note, "author")
        if author_ref:
            res["authorReference"] = author_ref
    return res


def _fhir_quantity(obj, prefix: str) -> dict | None:
    val = getattr(obj, f"{prefix}_value", None)
    if val is None:
        return None
    res: dict = {"value": float(val)}
    unit = getattr(obj, f"{prefix}_unit", None)
    system = getattr(obj, f"{prefix}_system", None)
    code = getattr(obj, f"{prefix}_code", None)
    if unit:
        res["unit"] = unit
    if system:
        res["system"] = system
    if code:
        res["code"] = code
    return res


def fhir_medication_statement_dosage(d: MedicationStatementDosage) -> dict:
    entry: dict = {}
    if d.sequence is not None:
        entry["sequence"] = d.sequence
    if d.text:
        entry["text"] = d.text
    additional_instructions = [
        fhir_medication_statement_codeable_concept(ai.codings, ai.text) for ai in (d.additional_instructions or [])
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
        as_needed_cc = fhir_medication_statement_codeable_concept(d.as_needed_codings, d.as_needed_codeable_concept_text)
        if as_needed_cc:
            entry["asNeededCodeableConcept"] = as_needed_cc

    site = fhir_medication_statement_codeable_concept(d.site_codings, d.site_text)
    if site:
        entry["site"] = site
    route = fhir_medication_statement_codeable_concept(d.route_codings, d.route_text)
    if route:
        entry["route"] = route
    method = fhir_medication_statement_codeable_concept(d.method_codings, d.method_text)
    if method:
        entry["method"] = method

    if d.dose_and_rate:
        entry["doseAndRate"] = list(d.dose_and_rate)
    if d.max_dose_per_period:
        entry["maxDosePerPeriod"] = dict(d.max_dose_per_period)

    max_dose_per_administration = _fhir_quantity(d, "max_dose_per_administration")
    if max_dose_per_administration:
        entry["maxDosePerAdministration"] = max_dose_per_administration
    max_dose_per_lifetime = _fhir_quantity(d, "max_dose_per_lifetime")
    if max_dose_per_lifetime:
        entry["maxDosePerLifetime"] = max_dose_per_lifetime

    return entry


def _fhir_meta(model: MedicationStatementModel) -> dict:
    meta: dict = {}
    if model.updated_at:
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    return meta


def to_fhir_medication_statement(model: MedicationStatementModel) -> dict:
    res: dict = {
        "resourceType": "MedicationStatement",
        "id": str(model.medication_statement_id),
        "status": fhir_enum(model.status),
    }

    meta = _fhir_meta(model)
    if meta:
        res["meta"] = meta

    if model.category_codings or model.category_text:
        cat = fhir_medication_statement_codeable_concept(model.category_codings, model.category_text)
        if cat:
            res["category"] = cat

    # medication[x] (1..1 choice)
    if model.medication_codings or model.medication_codeable_concept_text:
        med_cc = fhir_medication_statement_codeable_concept(
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

    # effective[x] (dateTime | Period)
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

    if model.date_asserted:
        res["dateAsserted"] = fhir_instant(model.date_asserted)

    # informationSource
    info_src = _fhir_reference_with_identifier_fallback(model, "information_source")
    if info_src:
        res["informationSource"] = info_src

    # basedOn
    bo_list = [fhir_medication_statement_based_on(b) for b in (model.based_on or [])]
    bo_list = [b for b in bo_list if b]
    if bo_list:
        res["basedOn"] = bo_list

    # partOf
    po_list = [fhir_medication_statement_part_of(p) for p in (model.part_of or [])]
    po_list = [p for p in po_list if p]
    if po_list:
        res["partOf"] = po_list

    # statusReason
    sr_list = [fhir_medication_statement_status_reason(sr) for sr in (model.status_reasons or [])]
    sr_list = [sr for sr in sr_list if sr]
    if sr_list:
        res["statusReason"] = sr_list

    # derivedFrom
    df_list = [fhir_medication_statement_derived_from(df) for df in (model.derived_from or [])]
    df_list = [df for df in df_list if df]
    if df_list:
        res["derivedFrom"] = df_list

    # reasonCode
    rc_list = [fhir_medication_statement_reason_code(rc) for rc in (model.reason_codes or [])]
    rc_list = [rc for rc in rc_list if rc]
    if rc_list:
        res["reasonCode"] = rc_list

    # reasonReference
    rr_list = [fhir_medication_statement_reason_reference(rr) for rr in (model.reason_references or [])]
    rr_list = [rr for rr in rr_list if rr]
    if rr_list:
        res["reasonReference"] = rr_list

    # note
    notes = [fhir_medication_statement_note(n) for n in (model.notes or [])]
    notes = [n for n in notes if n]
    if notes:
        res["note"] = notes

    # dosage
    dosages = [fhir_medication_statement_dosage(d) for d in (model.dosages or [])]
    dosages = [d for d in dosages if d]
    if dosages:
        res["dosage"] = dosages

    # identifier
    identifiers = [fhir_medication_statement_identifier(i) for i in (model.identifiers or [])]
    identifiers = [i for i in identifiers if i]
    if identifiers:
        res["identifier"] = identifiers

    if model.extension:
        res["extension"] = list(model.extension)

    return {k: v for k, v in res.items() if v is not None}
