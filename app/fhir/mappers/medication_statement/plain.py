from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.medication_statement import (
        MedicationStatementDosage,
        MedicationStatementIdentifier,
        MedicationStatementModel,
        MedicationStatementNote,
        MedicationStatementReasonCode,
        MedicationStatementStatusReason,
    )


def _plain_coding_list(codings) -> list[dict]:
    result = []
    for c in codings or []:
        result.append(
            {
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "user_selected": c.user_selected,
            }
        )
    return result


def plain_medication_statement_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _plain_coding_list(codings)
    if not coding_list and not text:
        return None
    return {
        "text": text,
        "coding": coding_list or None,
    }


def _plain_reference(obj, prefix: str, include_id: bool = False) -> dict | None:
    raw_reference = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

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

    has_any = (
        raw_reference
        or ref_type
        or ref_id
        or display
        or id_use
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
    )
    if not has_any:
        return None

    res: dict = {
        "reference": raw_reference or (f"{fhir_enum(ref_type)}/{ref_id}" if ref_type and ref_id else None),
        "reference_type": fhir_enum(ref_type) if ref_type else None,
        "reference_id": ref_id,
        "reference_display": display,
        "reference_identifier_use": fhir_enum(id_use) if id_use else None,
        "reference_identifier_type_system": id_type_system,
        "reference_identifier_type_version": id_type_version,
        "reference_identifier_type_code": id_type_code,
        "reference_identifier_type_display": id_type_display,
        "reference_identifier_type_user_selected": id_type_user_selected,
        "reference_identifier_type_text": id_type_text,
        "reference_identifier_system": id_system,
        "reference_identifier_value": id_value,
        "reference_identifier_period_start": id_period_start,
        "reference_identifier_period_end": id_period_end,
    }
    if include_id:
        res["id"] = obj.id
    return res


def plain_medication_statement_identifier(ident: MedicationStatementIdentifier) -> dict:
    assigner = _plain_reference(ident, "assigner")
    res = {
        "id": ident.id,
        "use": fhir_enum(ident.use) if ident.use else None,
        "type_text": ident.type_text,
        "system": ident.system,
        "value": ident.value,
        "period_start": ident.period_start,
        "period_end": ident.period_end,
        "type_codings": _plain_coding_list(ident.type_codings) or None,
    }
    if assigner:
        for k, v in assigner.items():
            res[f"assigner_{k}"] = v
    return res


def plain_medication_statement_based_on(bo) -> dict:
    return _plain_reference(bo, "reference", include_id=True) or {"id": bo.id}


def plain_medication_statement_part_of(po) -> dict:
    return _plain_reference(po, "reference", include_id=True) or {"id": po.id}


def plain_medication_statement_derived_from(df) -> dict:
    return _plain_reference(df, "reference", include_id=True) or {"id": df.id}


def plain_medication_statement_reason_reference(rr) -> dict:
    return _plain_reference(rr, "reference", include_id=True) or {"id": rr.id}


def plain_medication_statement_status_reason(sr: MedicationStatementStatusReason) -> dict:
    return {
        "id": sr.id,
        "text": sr.text,
        "coding": _plain_coding_list(sr.codings) or None,
    }


def plain_medication_statement_reason_code(rc: MedicationStatementReasonCode) -> dict:
    return {
        "id": rc.id,
        "text": rc.text,
        "coding": _plain_coding_list(rc.codings) or None,
    }


def plain_medication_statement_note(note: MedicationStatementNote) -> dict:
    author = _plain_reference(note, "author")
    res = {
        "id": note.id,
        "text": note.text,
        "time": note.time,
        "author_string": note.author_string,
    }
    if author:
        for k, v in author.items():
            res[f"author_{k}"] = v
    return res


def plain_medication_statement_dosage(d: MedicationStatementDosage) -> dict:
    return {
        "id": d.id,
        "sequence": d.sequence,
        "text": d.text,
        "additional_instruction": [
            {**(plain_medication_statement_codeable_concept(ai.codings, ai.text) or {}), "id": ai.id}
            for ai in (d.additional_instructions or [])
        ]
        or None,
        "patient_instruction": d.patient_instruction,
        "timing": dict(d.timing) if d.timing else None,
        "as_needed_boolean": d.as_needed_boolean,
        "as_needed_codeable_concept": plain_medication_statement_codeable_concept(
            d.as_needed_codings, d.as_needed_codeable_concept_text
        ),
        "site": plain_medication_statement_codeable_concept(d.site_codings, d.site_text),
        "route": plain_medication_statement_codeable_concept(d.route_codings, d.route_text),
        "method": plain_medication_statement_codeable_concept(d.method_codings, d.method_text),
        "dose_and_rate": list(d.dose_and_rate) if d.dose_and_rate else None,
        "max_dose_per_period": dict(d.max_dose_per_period) if d.max_dose_per_period else None,
        "max_dose_per_administration_value": float(d.max_dose_per_administration_value)
        if d.max_dose_per_administration_value is not None
        else None,
        "max_dose_per_administration_unit": d.max_dose_per_administration_unit,
        "max_dose_per_administration_system": d.max_dose_per_administration_system,
        "max_dose_per_administration_code": d.max_dose_per_administration_code,
        "max_dose_per_lifetime_value": float(d.max_dose_per_lifetime_value)
        if d.max_dose_per_lifetime_value is not None
        else None,
        "max_dose_per_lifetime_unit": d.max_dose_per_lifetime_unit,
        "max_dose_per_lifetime_system": d.max_dose_per_lifetime_system,
        "max_dose_per_lifetime_code": d.max_dose_per_lifetime_code,
    }


def to_plain_medication_statement(model: MedicationStatementModel) -> dict:
    return {
        "id": model.medication_statement_id,
        "extension": list(model.extension) if model.extension else None,
        "identifier": [plain_medication_statement_identifier(i) for i in (model.identifiers or [])] or None,
        "based_on": [plain_medication_statement_based_on(b) for b in (model.based_on or [])] or None,
        "part_of": [plain_medication_statement_part_of(p) for p in (model.part_of or [])] or None,
        "status": fhir_enum(model.status),
        "status_reason": [plain_medication_statement_status_reason(sr) for sr in (model.status_reasons or [])] or None,
        "category": plain_medication_statement_codeable_concept(model.category_codings, model.category_text),
        "medication_codeable_concept": plain_medication_statement_codeable_concept(
            model.medication_codings, model.medication_codeable_concept_text
        ),
        "medication_reference": _plain_reference(model, "medication"),
        "subject": _plain_reference(model, "subject"),
        "context": _plain_reference(model, "context"),
        "effective_date_time": model.effective_date_time,
        "effective_period_start": model.effective_period_start,
        "effective_period_end": model.effective_period_end,
        "date_asserted": model.date_asserted,
        "information_source": _plain_reference(model, "information_source"),
        "derived_from": [plain_medication_statement_derived_from(df) for df in (model.derived_from or [])] or None,
        "reason_code": [plain_medication_statement_reason_code(rc) for rc in (model.reason_codes or [])] or None,
        "reason_reference": [plain_medication_statement_reason_reference(rr) for rr in (model.reason_references or [])]
        or None,
        "note": [plain_medication_statement_note(n) for n in (model.notes or [])] or None,
        "dosage": [plain_medication_statement_dosage(d) for d in (model.dosages or [])] or None,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }
