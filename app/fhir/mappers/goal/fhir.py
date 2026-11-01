from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.goal import (
        GoalCategory,
        GoalIdentifier,
        GoalModel,
        GoalNote,
        GoalOutcomeCode,
        GoalTarget,
    )


def _format_date(d) -> str | None:
    if not d:
        return None
    return d.isoformat() if hasattr(d, "isoformat") else str(d)


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


def _fhir_reference(obj, prefix: str) -> dict | None:
    if obj is None:
        return None
    ref = getattr(obj, f"{prefix}_reference", None)
    rtype = getattr(obj, f"{prefix}_type", None)
    rid = getattr(obj, f"{prefix}_id", None)
    disp = getattr(obj, f"{prefix}_display", None)

    out: dict[str, Any] = {}
    if ref:
        out["reference"] = ref
    elif rtype and rid:
        type_str = fhir_enum(rtype)
        out["reference"] = f"{type_str}/{rid}"
    if disp:
        out["display"] = disp

    use = getattr(obj, f"{prefix}_identifier_use", None)
    val = getattr(obj, f"{prefix}_identifier_value", None)
    sys = getattr(obj, f"{prefix}_identifier_system", None)
    type_code = getattr(obj, f"{prefix}_identifier_type_code", None)
    p_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    p_end = getattr(obj, f"{prefix}_identifier_period_end", None)

    if (
        use
        or val
        or sys
        or type_code
        or p_start
        or p_end
        or getattr(obj, f"{prefix}_identifier_type_text", None)
    ):
        ident: dict[str, Any] = {}
        if use:
            ident["use"] = fhir_enum(use)
        if sys:
            ident["system"] = sys
        if val:
            ident["value"] = val
        if type_code or getattr(obj, f"{prefix}_identifier_type_text", None):
            coding: dict[str, Any] = {}
            if getattr(obj, f"{prefix}_identifier_type_system", None):
                coding["system"] = getattr(obj, f"{prefix}_identifier_type_system")
            if getattr(obj, f"{prefix}_identifier_type_version", None):
                coding["version"] = getattr(obj, f"{prefix}_identifier_type_version")
            if type_code:
                coding["code"] = type_code
            if getattr(obj, f"{prefix}_identifier_type_display", None):
                coding["display"] = getattr(obj, f"{prefix}_identifier_type_display")
            if getattr(obj, f"{prefix}_identifier_type_user_selected", None) is not None:
                coding["userSelected"] = getattr(obj, f"{prefix}_identifier_type_user_selected")

            type_dict: dict[str, Any] = {}
            if coding:
                type_dict["coding"] = [coding]
            if getattr(obj, f"{prefix}_identifier_type_text", None):
                type_dict["text"] = getattr(obj, f"{prefix}_identifier_type_text")
            if type_dict:
                ident["type"] = type_dict
        if p_start or p_end:
            period: dict[str, Any] = {}
            if p_start:
                period["start"] = fhir_instant(p_start)
            if p_end:
                period["end"] = fhir_instant(p_end)
            ident["period"] = period
        out["identifier"] = ident

    return out or None


def _fhir_reference_row(row) -> dict | None:
    return _fhir_reference(row, "reference")


def _fhir_identifier(i: GoalIdentifier) -> dict | None:
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
    assigner = _fhir_reference(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _fhir_note(n: GoalNote) -> dict | None:
    entry: dict = {}
    if n.author_string:
        entry["authorString"] = n.author_string
    else:
        author_ref = _fhir_reference(n, "author")
        if author_ref:
            entry["authorReference"] = author_ref
    if n.time:
        entry["time"] = fhir_instant(n.time)
    if n.text:
        entry["text"] = n.text
    return entry or None


def _fhir_target(t: GoalTarget) -> dict | None:
    entry: dict = {}
    measure = _fhir_codeable_concept(
        getattr(t, "measure_codings", None), t.measure_text
    )
    if measure:
        entry["measure"] = measure

    # detail[x]
    if t.detail_quantity_value is not None:
        q: dict = {"value": float(t.detail_quantity_value)}
        if t.detail_quantity_unit:
            q["unit"] = t.detail_quantity_unit
        if t.detail_quantity_system:
            q["system"] = t.detail_quantity_system
        if t.detail_quantity_code:
            q["code"] = t.detail_quantity_code
        if t.detail_quantity_comparator:
            q["comparator"] = t.detail_quantity_comparator
        entry["detailQuantity"] = q
    elif t.detail_range_low_value is not None or t.detail_range_high_value is not None:
        rng: dict = {}
        if t.detail_range_low_value is not None:
            low: dict = {"value": float(t.detail_range_low_value)}
            if t.detail_range_low_unit:
                low["unit"] = t.detail_range_low_unit
            if t.detail_range_low_system:
                low["system"] = t.detail_range_low_system
            if t.detail_range_low_code:
                low["code"] = t.detail_range_low_code
            rng["low"] = low
        if t.detail_range_high_value is not None:
            high: dict = {"value": float(t.detail_range_high_value)}
            if t.detail_range_high_unit:
                high["unit"] = t.detail_range_high_unit
            if t.detail_range_high_system:
                high["system"] = t.detail_range_high_system
            if t.detail_range_high_code:
                high["code"] = t.detail_range_high_code
            rng["high"] = high
        entry["detailRange"] = rng
    elif t.detail_codeable_concept_text or getattr(t, "detail_codings", None):
        cc = _fhir_codeable_concept(
            getattr(t, "detail_codings", None), t.detail_codeable_concept_text
        )
        if cc:
            entry["detailCodeableConcept"] = cc
    elif t.detail_string is not None:
        entry["detailString"] = t.detail_string
    elif t.detail_boolean is not None:
        entry["detailBoolean"] = t.detail_boolean
    elif t.detail_integer is not None:
        entry["detailInteger"] = t.detail_integer
    elif t.detail_ratio_numerator_value is not None or t.detail_ratio_denominator_value is not None:
        ratio: dict = {}
        if t.detail_ratio_numerator_value is not None:
            num: dict = {"value": float(t.detail_ratio_numerator_value)}
            if t.detail_ratio_numerator_unit:
                num["unit"] = t.detail_ratio_numerator_unit
            if t.detail_ratio_numerator_system:
                num["system"] = t.detail_ratio_numerator_system
            if t.detail_ratio_numerator_code:
                num["code"] = t.detail_ratio_numerator_code
            ratio["numerator"] = num
        if t.detail_ratio_denominator_value is not None:
            den: dict = {"value": float(t.detail_ratio_denominator_value)}
            if t.detail_ratio_denominator_unit:
                den["unit"] = t.detail_ratio_denominator_unit
            if t.detail_ratio_denominator_system:
                den["system"] = t.detail_ratio_denominator_system
            if t.detail_ratio_denominator_code:
                den["code"] = t.detail_ratio_denominator_code
            ratio["denominator"] = den
        entry["detailRatio"] = ratio

    # due[x]
    if t.due_date is not None:
        entry["dueDate"] = _format_date(t.due_date)
    elif t.due_duration_value is not None:
        dur: dict = {"value": float(t.due_duration_value)}
        if t.due_duration_unit:
            dur["unit"] = t.due_duration_unit
        if t.due_duration_system:
            dur["system"] = t.due_duration_system
        if t.due_duration_code:
            dur["code"] = t.due_duration_code
        entry["dueDuration"] = dur

    return entry or None


def _fhir_meta(model: GoalModel) -> dict | None:
    meta: dict[str, Any] = {}
    if getattr(model, "updated_at", None):
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    elif getattr(model, "created_at", None):
        meta["lastUpdated"] = fhir_instant(model.created_at)
    return meta or None


def to_fhir_goal(model: GoalModel) -> dict:
    """Serialize GoalModel to a FHIR R4 Goal resource dict."""
    result: dict[str, Any] = {
        "resourceType": "Goal",
        "id": str(model.goal_id),
        "lifecycleStatus": fhir_enum(model.lifecycle_status),
    }
    meta = _fhir_meta(model)
    if meta:
        result["meta"] = meta

    if model.identifiers:
        ids = [
            item
            for item in (_fhir_identifier(i) for i in model.identifiers)
            if item is not None
        ]
        if ids:
            result["identifier"] = ids

    achievement_status = _fhir_codeable_concept(
        model.achievement_status_codings, model.achievement_status_text
    )
    if achievement_status:
        result["achievementStatus"] = achievement_status

    if model.categories:
        categories = [
            item
            for item in (
                _fhir_codeable_concept(c.codings, c.text) for c in model.categories
            )
            if item is not None
        ]
        if categories:
            result["category"] = categories

    priority = _fhir_codeable_concept(
        model.priority_codings, model.priority_text
    )
    if priority:
        result["priority"] = priority

    description = _fhir_codeable_concept(
        model.description_codings, model.description_text
    )
    if description:
        result["description"] = description

    subject = _fhir_reference(model, "subject")
    if subject:
        result["subject"] = subject

    if model.start_date is not None:
        result["startDate"] = _format_date(model.start_date)
    elif model.start_codeable_concept_text or model.start_codings:
        start_cc = _fhir_codeable_concept(
            model.start_codings, model.start_codeable_concept_text
        )
        if start_cc:
            result["startCodeableConcept"] = start_cc

    if model.targets:
        targets = [
            item
            for item in (_fhir_target(t) for t in model.targets)
            if item is not None
        ]
        if targets:
            result["target"] = targets

    if model.status_date is not None:
        result["statusDate"] = _format_date(model.status_date)

    if model.status_reason:
        result["statusReason"] = model.status_reason

    expressed_by = _fhir_reference(model, "expressed_by")
    if expressed_by:
        result["expressedBy"] = expressed_by

    if model.addresses_list:
        addresses = [
            item
            for item in (_fhir_reference_row(a) for a in model.addresses_list)
            if item is not None
        ]
        if addresses:
            result["addresses"] = addresses

    if model.notes:
        notes = [
            item
            for item in (_fhir_note(n) for n in model.notes)
            if item is not None
        ]
        if notes:
            result["note"] = notes

    if model.outcome_codes:
        outcome_codes = [
            item
            for item in (
                _fhir_codeable_concept(oc.codings, oc.text)
                for oc in model.outcome_codes
            )
            if item is not None
        ]
        if outcome_codes:
            result["outcomeCode"] = outcome_codes

    if model.outcome_references:
        outcome_refs = [
            item
            for item in (
                _fhir_reference_row(o) for o in model.outcome_references
            )
            if item is not None
        ]
        if outcome_refs:
            result["outcomeReference"] = outcome_refs

    if model.extension:
        result["extension"] = model.extension

    return {k: v for k, v in result.items() if v is not None}
