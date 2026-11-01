"""Payload -> FHIR JSON conversion for Goal.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(GoalCreateSchema / GoalPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.schemas.goal.input import (
        GoalCategoryInput,
        GoalCreateSchema,
        GoalIdentifierInput,
        GoalNoteInput,
        GoalPatchSchema,
        GoalReferenceInput,
        GoalTargetInput,
    )


def _format_date(d) -> str | None:
    if not d:
        return None
    return d.isoformat() if hasattr(d, "isoformat") else str(d)


from app.repository._reference_shared import _IDENTIFIER_FALLBACK_SUFFIXES

_ACHIEVEMENT_STATUS_FIELDS = {"achievement_status_coding", "achievement_status_text"}
_PRIORITY_FIELDS = {"priority_coding", "priority_text"}
_DESCRIPTION_FIELDS = {"description_coding", "description_text"}
_SUBJECT_FIELDS = {"subject", "subject_display"} | {
    f"subject_{s}" for s in _IDENTIFIER_FALLBACK_SUFFIXES
}
_START_CC_FIELDS = {"start_codeable_concept_coding", "start_codeable_concept_text"}
_EXPRESSED_BY_FIELDS = {"expressed_by", "expressed_by_display"} | {
    f"expressed_by_{s}" for s in _IDENTIFIER_FALLBACK_SUFFIXES
}


def _coding_from_payload(c: Any) -> dict:
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


def _codeable_concept_from_payload(
    codings: list | None, text: str | None
) -> dict | None:
    coding_list = [_coding_from_payload(c) for c in (codings or [])]
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _reference_from_payload(obj: Any, prefix: str) -> dict | None:
    def _get(field):
        return obj.get(field) if isinstance(obj, dict) else getattr(obj, field, None)

    raw_reference = _get(prefix)
    display = _get(f"{prefix}_display")

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    if display:
        entry["display"] = display

    id_use = _get(f"{prefix}_identifier_use")
    id_type_system = _get(f"{prefix}_identifier_type_system")
    id_type_version = _get(f"{prefix}_identifier_type_version")
    id_type_code = _get(f"{prefix}_identifier_type_code")
    id_type_display = _get(f"{prefix}_identifier_type_display")
    id_type_text = _get(f"{prefix}_identifier_type_text")
    id_type_user_selected = _get(f"{prefix}_identifier_type_user_selected")
    id_system = _get(f"{prefix}_identifier_system")
    id_value = _get(f"{prefix}_identifier_value")
    id_period_start = _get(f"{prefix}_identifier_period_start")
    id_period_end = _get(f"{prefix}_identifier_period_end")

    if id_use or id_type_system or id_type_code or id_type_text or id_system or id_value:
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
        if id_type_system or id_type_code or id_type_text:
            type_cc: dict = {}
            if id_type_system or id_type_code:
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
                    "start": fhir_instant(id_period_start),
                    "end": fhir_instant(id_period_end),
                }.items()
                if v
            }
        entry["identifier"] = identifier
    return entry or None


def _ref_from_payload(ref: Any, display: str | None = None) -> dict | None:
    if not ref and not display:
        return None
    if isinstance(ref, str):
        result = {"reference": ref}
        if display:
            result["display"] = display
        return result

    result = {}
    r = getattr(ref, "reference", None) if not isinstance(ref, dict) else ref.get("reference")
    if r:
        result["reference"] = r
    d = (getattr(ref, "display", None) if not isinstance(ref, dict) else ref.get("display")) or display
    if d:
        result["display"] = d

    def _get(field):
        return ref.get(field) if isinstance(ref, dict) else getattr(ref, field, None)

    id_use = _get("identifier_use")
    id_type_system = _get("identifier_type_system")
    id_type_version = _get("identifier_type_version")
    id_type_code = _get("identifier_type_code")
    id_type_display = _get("identifier_type_display")
    id_type_text = _get("identifier_type_text")
    id_type_user_selected = _get("identifier_type_user_selected")
    id_system = _get("identifier_system")
    id_value = _get("identifier_value")
    id_period_start = _get("identifier_period_start")
    id_period_end = _get("identifier_period_end")

    if id_use or id_type_system or id_type_code or id_type_text or id_system or id_value:
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
        if id_type_system or id_type_code or id_type_text:
            type_cc: dict = {}
            if id_type_system or id_type_code:
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
                    "start": fhir_instant(id_period_start),
                    "end": fhir_instant(id_period_end),
                }.items()
                if v
            }
        result["identifier"] = identifier
    return result or None


def _identifier_from_payload(i: Any) -> dict | None:
    if not i:
        return None
    if isinstance(i, dict):
        use = i.get("use")
        type_coding = i.get("type_coding")
        type_text = i.get("type_text")
        system = i.get("system")
        value = i.get("value")
        p_start = i.get("period_start")
        p_end = i.get("period_end")
    else:
        use = getattr(i, "use", None)
        type_coding = getattr(i, "type_coding", None)
        type_text = getattr(i, "type_text", None)
        system = getattr(i, "system", None)
        value = getattr(i, "value", None)
        p_start = getattr(i, "period_start", None)
        p_end = getattr(i, "period_end", None)

    entry: dict = {}
    if use:
        entry["use"] = fhir_enum(use)
    type_cc = _codeable_concept_from_payload(type_coding, type_text)
    if type_cc:
        entry["type"] = type_cc
    if system:
        entry["system"] = system
    if value:
        entry["value"] = value
    if p_start or p_end:
        period: dict = {}
        if p_start:
            period["start"] = fhir_instant(p_start)
        if p_end:
            period["end"] = fhir_instant(p_end)
        entry["period"] = period
    assigner_ref = _reference_from_payload(i, "assigner")
    if assigner_ref:
        entry["assigner"] = assigner_ref
    return entry or None


def _category_from_payload(c: Any) -> dict | None:
    if not c:
        return None
    if isinstance(c, dict):
        return _codeable_concept_from_payload(c.get("coding"), c.get("text"))
    return _codeable_concept_from_payload(
        getattr(c, "coding", None), getattr(c, "text", None)
    )


def _note_from_payload(n: Any) -> dict | None:
    if not n:
        return None
    if isinstance(n, str):
        return {"text": n}
    if isinstance(n, dict):
        entry: dict = {}
        if n.get("author_string"):
            entry["authorString"] = n["author_string"]
        else:
            ref = _reference_from_payload(n, "author")
            if ref:
                entry["authorReference"] = ref
        if n.get("time"):
            entry["time"] = fhir_instant(n["time"])
        if n.get("text"):
            entry["text"] = n["text"]
        return entry or None
    entry = {}
    if getattr(n, "author_string", None):
        entry["authorString"] = n.author_string
    else:
        ref = _reference_from_payload(n, "author")
        if ref:
            entry["authorReference"] = ref
    if getattr(n, "time", None):
        entry["time"] = fhir_instant(n.time)
    if getattr(n, "text", None):
        entry["text"] = n.text
    return entry or None


def _target_from_payload(t: Any) -> dict | None:
    if not t:
        return None
    entry: dict = {}

    measure_coding = getattr(t, "measure_coding", None) or (
        t.get("measure_coding") if isinstance(t, dict) else None
    )
    measure_text = getattr(t, "measure_text", None) or (
        t.get("measure_text") if isinstance(t, dict) else None
    )
    measure = _codeable_concept_from_payload(measure_coding, measure_text)
    if measure:
        entry["measure"] = measure

    # detailQuantity
    detail_quantity_value = getattr(t, "detail_quantity_value", None) or (
        t.get("detail_quantity_value") if isinstance(t, dict) else None
    )
    if detail_quantity_value is not None:
        q: dict = {"value": float(detail_quantity_value)}
        unit = getattr(t, "detail_quantity_unit", None) or (
            t.get("detail_quantity_unit") if isinstance(t, dict) else None
        )
        system = getattr(t, "detail_quantity_system", None) or (
            t.get("detail_quantity_system") if isinstance(t, dict) else None
        )
        code = getattr(t, "detail_quantity_code", None) or (
            t.get("detail_quantity_code") if isinstance(t, dict) else None
        )
        comp = getattr(t, "detail_quantity_comparator", None) or (
            t.get("detail_quantity_comparator") if isinstance(t, dict) else None
        )
        if unit:
            q["unit"] = unit
        if system:
            q["system"] = system
        if code:
            q["code"] = code
        if comp:
            q["comparator"] = comp
        entry["detailQuantity"] = q
    else:
        # detailRange
        detail_range_low_value = getattr(t, "detail_range_low_value", None) or (
            t.get("detail_range_low_value") if isinstance(t, dict) else None
        )
        detail_range_high_value = getattr(t, "detail_range_high_value", None) or (
            t.get("detail_range_high_value") if isinstance(t, dict) else None
        )
        if detail_range_low_value is not None or detail_range_high_value is not None:
            rng: dict = {}
            if detail_range_low_value is not None:
                low: dict = {"value": float(detail_range_low_value)}
                low_u = getattr(t, "detail_range_low_unit", None) or (
                    t.get("detail_range_low_unit") if isinstance(t, dict) else None
                )
                low_s = getattr(t, "detail_range_low_system", None) or (
                    t.get("detail_range_low_system") if isinstance(t, dict) else None
                )
                low_c = getattr(t, "detail_range_low_code", None) or (
                    t.get("detail_range_low_code") if isinstance(t, dict) else None
                )
                if low_u:
                    low["unit"] = low_u
                if low_s:
                    low["system"] = low_s
                if low_c:
                    low["code"] = low_c
                rng["low"] = low
            if detail_range_high_value is not None:
                high: dict = {"value": float(detail_range_high_value)}
                high_u = getattr(t, "detail_range_high_unit", None) or (
                    t.get("detail_range_high_unit") if isinstance(t, dict) else None
                )
                high_s = getattr(t, "detail_range_high_system", None) or (
                    t.get("detail_range_high_system") if isinstance(t, dict) else None
                )
                high_c = getattr(t, "detail_range_high_code", None) or (
                    t.get("detail_range_high_code") if isinstance(t, dict) else None
                )
                if high_u:
                    high["unit"] = high_u
                if high_s:
                    high["system"] = high_s
                if high_c:
                    high["code"] = high_c
                rng["high"] = high
            entry["detailRange"] = rng
        else:
            # detailCodeableConcept
            detail_cc_coding = getattr(t, "detail_codeable_concept_coding", None) or (
                t.get("detail_codeable_concept_coding") if isinstance(t, dict) else None
            )
            detail_cc_text = getattr(t, "detail_codeable_concept_text", None) or (
                t.get("detail_codeable_concept_text") if isinstance(t, dict) else None
            )
            if detail_cc_coding or detail_cc_text:
                cc = _codeable_concept_from_payload(detail_cc_coding, detail_cc_text)
                if cc:
                    entry["detailCodeableConcept"] = cc
            else:
                detail_string = getattr(t, "detail_string", None) or (
                    t.get("detail_string") if isinstance(t, dict) else None
                )
                if detail_string is not None:
                    entry["detailString"] = detail_string
                else:
                    detail_boolean = (
                        t.get("detail_boolean")
                        if isinstance(t, dict)
                        else getattr(t, "detail_boolean", None)
                    )
                    if detail_boolean is not None:
                        entry["detailBoolean"] = detail_boolean
                    else:
                        detail_integer = getattr(t, "detail_integer", None) or (
                            t.get("detail_integer") if isinstance(t, dict) else None
                        )
                        if detail_integer is not None:
                            entry["detailInteger"] = detail_integer
                        else:
                            detail_ratio_num_val = getattr(
                                t, "detail_ratio_numerator_value", None
                            ) or (
                                t.get("detail_ratio_numerator_value")
                                if isinstance(t, dict)
                                else None
                            )
                            detail_ratio_den_val = getattr(
                                t, "detail_ratio_denominator_value", None
                            ) or (
                                t.get("detail_ratio_denominator_value")
                                if isinstance(t, dict)
                                else None
                            )
                            if (
                                detail_ratio_num_val is not None
                                or detail_ratio_den_val is not None
                            ):
                                ratio: dict = {}
                                if detail_ratio_num_val is not None:
                                    num: dict = {"value": float(detail_ratio_num_val)}
                                    nu = getattr(
                                        t, "detail_ratio_numerator_unit", None
                                    ) or (
                                        t.get("detail_ratio_numerator_unit")
                                        if isinstance(t, dict)
                                        else None
                                    )
                                    ns = getattr(
                                        t, "detail_ratio_numerator_system", None
                                    ) or (
                                        t.get("detail_ratio_numerator_system")
                                        if isinstance(t, dict)
                                        else None
                                    )
                                    nc = getattr(
                                        t, "detail_ratio_numerator_code", None
                                    ) or (
                                        t.get("detail_ratio_numerator_code")
                                        if isinstance(t, dict)
                                        else None
                                    )
                                    if nu:
                                        num["unit"] = nu
                                    if ns:
                                        num["system"] = ns
                                    if nc:
                                        num["code"] = nc
                                    ratio["numerator"] = num
                                if detail_ratio_den_val is not None:
                                    den: dict = {"value": float(detail_ratio_den_val)}
                                    du = getattr(
                                        t, "detail_ratio_denominator_unit", None
                                    ) or (
                                        t.get("detail_ratio_denominator_unit")
                                        if isinstance(t, dict)
                                        else None
                                    )
                                    ds = getattr(
                                        t, "detail_ratio_denominator_system", None
                                    ) or (
                                        t.get("detail_ratio_denominator_system")
                                        if isinstance(t, dict)
                                        else None
                                    )
                                    dc = getattr(
                                        t, "detail_ratio_denominator_code", None
                                    ) or (
                                        t.get("detail_ratio_denominator_code")
                                        if isinstance(t, dict)
                                        else None
                                    )
                                    if du:
                                        den["unit"] = du
                                    if ds:
                                        den["system"] = ds
                                    if dc:
                                        den["code"] = dc
                                    ratio["denominator"] = den
                                entry["detailRatio"] = ratio

    # due[x]
    due_date = getattr(t, "due_date", None) or (
        t.get("due_date") if isinstance(t, dict) else None
    )
    if due_date is not None:
        entry["dueDate"] = _format_date(due_date)
    else:
        due_dur_val = getattr(t, "due_duration_value", None) or (
            t.get("due_duration_value") if isinstance(t, dict) else None
        )
        if due_dur_val is not None:
            dur: dict = {"value": float(due_dur_val)}
            du = getattr(t, "due_duration_unit", None) or (
                t.get("due_duration_unit") if isinstance(t, dict) else None
            )
            ds = getattr(t, "due_duration_system", None) or (
                t.get("due_duration_system") if isinstance(t, dict) else None
            )
            dc = getattr(t, "due_duration_code", None) or (
                t.get("due_duration_code") if isinstance(t, dict) else None
            )
            if du:
                dur["unit"] = du
            if ds:
                dur["system"] = ds
            if dc:
                dur["code"] = dc
            entry["dueDuration"] = dur

    return entry or None


def payload_to_fhir_goal(payload: GoalCreateSchema) -> dict:
    """Convert a GoalCreateSchema to a full FHIR Goal dict."""
    result: dict[str, Any] = {
        "resourceType": "Goal",
        "id": "placeholder",
        "lifecycleStatus": fhir_enum(payload.lifecycle_status),
    }

    if payload.identifier:
        ids = [
            item
            for item in (_identifier_from_payload(i) for i in payload.identifier)
            if item is not None
        ]
        if ids:
            result["identifier"] = ids

    achievement_status = _codeable_concept_from_payload(
        payload.achievement_status_coding, payload.achievement_status_text
    )
    if achievement_status:
        result["achievementStatus"] = achievement_status

    if payload.category:
        categories = [
            item
            for item in (_category_from_payload(c) for c in payload.category)
            if item is not None
        ]
        if categories:
            result["category"] = categories

    priority = _codeable_concept_from_payload(
        payload.priority_coding, payload.priority_text
    )
    if priority:
        result["priority"] = priority

    description = _codeable_concept_from_payload(
        payload.description_coding, payload.description_text
    )
    if description:
        result["description"] = description

    subject = _reference_from_payload(payload, "subject")
    if subject:
        result["subject"] = subject

    if payload.start_date is not None:
        result["startDate"] = _format_date(payload.start_date)
    elif payload.start_codeable_concept_text or payload.start_codeable_concept_coding:
        start_cc = _codeable_concept_from_payload(
            payload.start_codeable_concept_coding, payload.start_codeable_concept_text
        )
        if start_cc:
            result["startCodeableConcept"] = start_cc

    if payload.target:
        targets = [
            item
            for item in (_target_from_payload(t) for t in payload.target)
            if item is not None
        ]
        if targets:
            result["target"] = targets

    if payload.status_date is not None:
        result["statusDate"] = _format_date(payload.status_date)

    if payload.status_reason:
        result["statusReason"] = payload.status_reason

    expressed_by = _reference_from_payload(payload, "expressed_by")
    if expressed_by:
        result["expressedBy"] = expressed_by

    if payload.addresses:
        addresses = [
            item
            for item in (_ref_from_payload(a) for a in payload.addresses)
            if item is not None
        ]
        if addresses:
            result["addresses"] = addresses

    if payload.note:
        notes = [
            item
            for item in (_note_from_payload(n) for n in payload.note)
            if item is not None
        ]
        if notes:
            result["note"] = notes

    if payload.outcome_code:
        outcome_codes = [
            item
            for item in (_category_from_payload(oc) for oc in payload.outcome_code)
            if item is not None
        ]
        if outcome_codes:
            result["outcomeCode"] = outcome_codes

    if payload.outcome_reference:
        outcome_refs = [
            item
            for item in (_ref_from_payload(o) for o in payload.outcome_reference)
            if item is not None
        ]
        if outcome_refs:
            result["outcomeReference"] = outcome_refs

    if payload.extension:
        result["extension"] = payload.extension

    return {k: v for k, v in result.items() if v is not None}


def patch_fragment_to_fhir_goal(
    payload: GoalPatchSchema,
) -> tuple[dict, set[str]]:
    """Convert a GoalPatchSchema to a partial FHIR dict and set of touched FHIR top-level keys."""
    fragment: dict[str, Any] = {}
    touched: set[str] = set()
    fields_set = payload.model_fields_set

    if "lifecycle_status" in fields_set:
        touched.add("lifecycleStatus")
        if payload.lifecycle_status is not None:
            fragment["lifecycleStatus"] = fhir_enum(payload.lifecycle_status)

    if _ACHIEVEMENT_STATUS_FIELDS & fields_set:
        touched.add("achievementStatus")
        achievement_status = _codeable_concept_from_payload(
            payload.achievement_status_coding, payload.achievement_status_text
        )
        if achievement_status:
            fragment["achievementStatus"] = achievement_status

    if "category" in fields_set:
        touched.add("category")
        if payload.category is not None:
            fragment["category"] = [
                item
                for item in (_category_from_payload(c) for c in payload.category)
                if item is not None
            ]

    if _PRIORITY_FIELDS & fields_set:
        touched.add("priority")
        priority = _codeable_concept_from_payload(
            payload.priority_coding, payload.priority_text
        )
        if priority:
            fragment["priority"] = priority

    if _DESCRIPTION_FIELDS & fields_set:
        touched.add("description")
        description = _codeable_concept_from_payload(
            payload.description_coding, payload.description_text
        )
        if description:
            fragment["description"] = description

    if _SUBJECT_FIELDS & fields_set:
        touched.add("subject")
        subject = _reference_from_payload(payload, "subject")
        if subject:
            fragment["subject"] = subject

    if "start_date" in fields_set:
        touched.add("startDate")
        if payload.start_date is not None:
            fragment["startDate"] = _format_date(payload.start_date)

    if _START_CC_FIELDS & fields_set:
        touched.add("startCodeableConcept")
        start_cc = _codeable_concept_from_payload(
            payload.start_codeable_concept_coding, payload.start_codeable_concept_text
        )
        if start_cc:
            fragment["startCodeableConcept"] = start_cc

    if "target" in fields_set:
        touched.add("target")
        if payload.target is not None:
            fragment["target"] = [
                item
                for item in (_target_from_payload(t) for t in payload.target)
                if item is not None
            ]

    if "status_date" in fields_set:
        touched.add("statusDate")
        if payload.status_date is not None:
            fragment["statusDate"] = _format_date(payload.status_date)

    if "status_reason" in fields_set:
        touched.add("statusReason")
        if payload.status_reason is not None:
            fragment["statusReason"] = payload.status_reason

    if _EXPRESSED_BY_FIELDS & fields_set:
        touched.add("expressedBy")
        expressed_by = _reference_from_payload(payload, "expressed_by")
        if expressed_by:
            fragment["expressedBy"] = expressed_by

    if "addresses" in fields_set:
        touched.add("addresses")
        if payload.addresses is not None:
            fragment["addresses"] = [
                item
                for item in (_ref_from_payload(a) for a in payload.addresses)
                if item is not None
            ]

    if "note" in fields_set:
        touched.add("note")
        if payload.note is not None:
            fragment["note"] = [
                item
                for item in (_note_from_payload(n) for n in payload.note)
                if item is not None
            ]

    if "outcome_code" in fields_set:
        touched.add("outcomeCode")
        if payload.outcome_code is not None:
            fragment["outcomeCode"] = [
                item
                for item in (_category_from_payload(oc) for oc in payload.outcome_code)
                if item is not None
            ]

    if "outcome_reference" in fields_set:
        touched.add("outcomeReference")
        if payload.outcome_reference is not None:
            fragment["outcomeReference"] = [
                item
                for item in (_ref_from_payload(o) for o in payload.outcome_reference)
                if item is not None
            ]

    if "identifier" in fields_set:
        touched.add("identifier")
        if payload.identifier is not None:
            fragment["identifier"] = [
                item
                for item in (_identifier_from_payload(i) for i in payload.identifier)
                if item is not None
            ]

    if "extension" in fields_set:
        touched.add("extension")
        if payload.extension is not None:
            fragment["extension"] = payload.extension

    return fragment, touched
