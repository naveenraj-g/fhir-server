from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

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


def plain_medication_dispense_codeable_concept(codings, text: str | None) -> dict | None:
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


def plain_medication_dispense_identifier(i: MedicationDispenseIdentifier) -> dict:
    entry: dict = {
        "id": i.id,
        "use": fhir_enum(i.use) if i.use else None,
        "type": plain_medication_dispense_codeable_concept(i.type_codings, i.type_text),
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start,
        "period_end": i.period_end,
    }
    assigner = _plain_reference(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return {k: v for k, v in entry.items() if v is not None}


def _plain_quantity(obj, prefix: str) -> dict | None:
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


def plain_medication_dispense_performer(p: MedicationDispensePerformer) -> dict:
    return {
        "id": p.id,
        "function": plain_medication_dispense_codeable_concept(
            p.function_codings, p.function_text
        ),
        "actor": _plain_reference(p, "actor"),
    }


def plain_medication_dispense_note(n: MedicationDispenseNote) -> dict:
    author_ref = _plain_reference(n, "author")
    entry: dict = {
        "id": n.id,
        "text": n.text,
        "time": n.time,
        "author_string": n.author_string,
        "author_reference": author_ref if author_ref else None,
    }
    return {k: v for k, v in entry.items() if v is not None}


def plain_medication_dispense_dosage(d: MedicationDispenseDosageInstruction) -> dict:
    additional_instructions = [
        plain_medication_dispense_codeable_concept(ai.codings, ai.text)
        for ai in (d.additional_instructions or [])
    ]
    additional_instructions = [ai for ai in additional_instructions if ai]

    return {
        "id": d.id,
        "sequence": d.sequence,
        "text": d.text,
        "additional_instruction": additional_instructions or None,
        "patient_instruction": d.patient_instruction,
        "timing": dict(d.timing) if d.timing else None,
        "as_needed_boolean": d.as_needed_boolean,
        "as_needed_codeable_concept": plain_medication_dispense_codeable_concept(
            d.as_needed_codings, d.as_needed_codeable_concept_text
        ),
        "site": plain_medication_dispense_codeable_concept(d.site_codings, d.site_text),
        "route": plain_medication_dispense_codeable_concept(d.route_codings, d.route_text),
        "method": plain_medication_dispense_codeable_concept(d.method_codings, d.method_text),
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


def _plain_substitution(md: MedicationDispenseModel) -> dict | None:
    has_sub = (
        md.substitution_was_substituted is not None
        or md.substitution_type_text
        or md.substitution_type_codings
        or md.substitution_reasons
        or md.substitution_responsible_parties
    )
    if not has_sub:
        return None

    reasons = [
        plain_medication_dispense_codeable_concept(r.codings, r.text)
        for r in (md.substitution_reasons or [])
    ]
    reasons = [r for r in reasons if r]

    parties = [
        {**_plain_reference(rp, "reference"), "id": rp.id}
        for rp in (md.substitution_responsible_parties or [])
    ]
    parties = [p for p in parties if p]

    return {
        "was_substituted": md.substitution_was_substituted,
        "type": plain_medication_dispense_codeable_concept(
            md.substitution_type_codings, md.substitution_type_text
        ),
        "reason": reasons or None,
        "responsible_party": parties or None,
    }


def to_plain_medication_dispense(md: MedicationDispenseModel) -> dict:
    """Format a MedicationDispenseModel as a plain snake_case dict."""
    status_reason_ref = _plain_reference(md, "status_reason_reference")
    medication_ref = _plain_reference(md, "medication")
    subject = _plain_reference(md, "subject")
    context = _plain_reference(md, "context")
    location = _plain_reference(md, "location")
    destination = _plain_reference(md, "destination")

    res = {
        "id": md.medication_dispense_id,
        "extension": list(md.extension) if md.extension else None,
        "identifier": [
            plain_medication_dispense_identifier(i) for i in (md.identifiers or [])
        ]
        or None,
        "part_of": [
            {**_plain_reference(p, "reference"), "id": p.id}
            for p in (md.part_of or [])
        ]
        or None,
        "status": fhir_enum(md.status),
        "status_reason_codeable_concept": plain_medication_dispense_codeable_concept(
            md.status_reason_codings, md.status_reason_codeable_concept_text
        ),
        "status_reason_reference": status_reason_ref if status_reason_ref else None,
        "category": plain_medication_dispense_codeable_concept(
            md.category_codings, md.category_text
        ),
        "medication_codeable_concept": plain_medication_dispense_codeable_concept(
            md.medication_codings, md.medication_codeable_concept_text
        ),
        "medication_reference": medication_ref if medication_ref else None,
        "subject": subject if subject else None,
        "context": context if context else None,
        "supporting_information": [
            {**_plain_reference(s, "reference"), "id": s.id}
            for s in (md.supporting_informations or [])
        ]
        or None,
        "performer": [
            plain_medication_dispense_performer(p) for p in (md.performers or [])
        ]
        or None,
        "location": location if location else None,
        "authorizing_prescription": [
            {**_plain_reference(a, "reference"), "id": a.id}
            for a in (md.authorizing_prescriptions or [])
        ]
        or None,
        "type": plain_medication_dispense_codeable_concept(
            md.type_codings, md.type_text
        ),
        "quantity": _plain_quantity(md, "quantity"),
        "days_supply": _plain_quantity(md, "days_supply"),
        "when_prepared": md.when_prepared,
        "when_handed_over": md.when_handed_over,
        "destination": destination if destination else None,
        "receiver": [
            {**_plain_reference(r, "reference"), "id": r.id}
            for r in (md.receivers or [])
        ]
        or None,
        "note": [plain_medication_dispense_note(n) for n in (md.notes or [])] or None,
        "dosage_instruction": [
            plain_medication_dispense_dosage(d) for d in (md.dosage_instructions or [])
        ]
        or None,
        "substitution": _plain_substitution(md),
        "detected_issue": [
            {**_plain_reference(d, "reference"), "id": d.id}
            for d in (md.detected_issues or [])
        ]
        or None,
        "event_history": [
            {**_plain_reference(e, "reference"), "id": e.id}
            for e in (md.event_history or [])
        ]
        or None,
    }
    return {k: v for k, v in res.items() if v is not None}
