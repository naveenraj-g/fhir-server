"""Payload -> FHIR JSON conversion for FamilyMemberHistory.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(FamilyMemberHistoryCreateSchema / FamilyMemberHistoryPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import merge_patch_fragment

if TYPE_CHECKING:
    from app.schemas.family_member_history.input import (
        FamilyMemberHistoryCodeableConceptInput,
        FamilyMemberHistoryConditionInput,
        FamilyMemberHistoryCreateSchema,
        FamilyMemberHistoryIdentifierInput,
        FamilyMemberHistoryNoteInput,
        FamilyMemberHistoryPatchSchema,
        FamilyMemberHistoryReasonCodeInput,
        FamilyMemberHistoryReasonReferenceInput,
    )

_COMPARATOR_SYMBOLS = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}

_IDENTIFIER_FALLBACK_SUFFIXES = [
    "identifier_use",
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
]

_PATIENT_FIELDS = {"patient", "patient_display"} | {
    f"patient_{s}" for s in _IDENTIFIER_FALLBACK_SUFFIXES
}

_BORN_FIELDS = {
    "born_period_start",
    "born_period_end",
    "born_date",
    "born_string",
}
_BORN_FHIR_KEYS = {"bornPeriod", "bornDate", "bornString"}

_AGE_FIELDS = {
    "age_age_value",
    "age_age_comparator",
    "age_age_unit",
    "age_age_system",
    "age_age_code",
    "age_range_low_value",
    "age_range_low_unit",
    "age_range_low_system",
    "age_range_low_code",
    "age_range_high_value",
    "age_range_high_unit",
    "age_range_high_system",
    "age_range_high_code",
    "age_string",
}
_AGE_FHIR_KEYS = {"ageAge", "ageRange", "ageString"}

_DECEASED_FIELDS = {
    "deceased_boolean",
    "deceased_age_value",
    "deceased_age_comparator",
    "deceased_age_unit",
    "deceased_age_system",
    "deceased_age_code",
    "deceased_range_low_value",
    "deceased_range_low_unit",
    "deceased_range_low_system",
    "deceased_range_low_code",
    "deceased_range_high_value",
    "deceased_range_high_unit",
    "deceased_range_high_system",
    "deceased_range_high_code",
    "deceased_date",
    "deceased_string",
}
_DECEASED_FHIR_KEYS = {
    "deceasedBoolean",
    "deceasedAge",
    "deceasedRange",
    "deceasedDate",
    "deceasedString",
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
                "userSelected": c.get("user_selected"),
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


def payload_family_member_history_codeable_concept(
    concept: FamilyMemberHistoryCodeableConceptInput | dict | None,
) -> dict | None:
    if not concept:
        return None
    if isinstance(concept, dict):
        codings = [_coding_from_payload(c) for c in (concept.get("coding") or [])]
        codings = [c for c in codings if c]
        text = concept.get("text")
    else:
        codings = [_coding_from_payload(c) for c in (concept.coding or [])]
        codings = [c for c in codings if c]
        text = concept.text

    result: dict = {}
    if codings:
        result["coding"] = codings
    if text:
        result["text"] = text
    return result or None


def _reference_with_identifier_from_payload(payload: Any, prefix: str) -> dict | None:
    if payload is None:
        return None
    ref_val = getattr(payload, prefix, None) if not isinstance(payload, dict) else payload.get(prefix)
    disp_val = getattr(payload, f"{prefix}_display", None) if not isinstance(payload, dict) else payload.get(f"{prefix}_display")

    entry: dict = {}
    if ref_val:
        entry["reference"] = ref_val
    if disp_val:
        entry["display"] = disp_val

    def _get(key):
        return getattr(payload, key, None) if not isinstance(payload, dict) else payload.get(key)

    id_use = _get(f"{prefix}_identifier_use")
    id_type_system = _get(f"{prefix}_identifier_type_system")
    id_type_version = _get(f"{prefix}_identifier_type_version")
    id_type_code = _get(f"{prefix}_identifier_type_code")
    id_type_display = _get(f"{prefix}_identifier_type_display")
    id_type_user_selected = _get(f"{prefix}_identifier_type_user_selected")
    id_type_text = _get(f"{prefix}_identifier_type_text")
    id_system = _get(f"{prefix}_identifier_system")
    id_value = _get(f"{prefix}_identifier_value")
    id_period_start = _get(f"{prefix}_identifier_period_start")
    id_period_end = _get(f"{prefix}_identifier_period_end")

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
            identifier["use"] = id_use.value if hasattr(id_use, "value") else str(id_use)
        if (
            id_type_system
            or id_type_code
            or id_type_display
            or id_type_version
            or id_type_user_selected
            or id_type_text
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
                    "start": id_period_start.isoformat() if hasattr(id_period_start, "isoformat") else id_period_start,
                    "end": id_period_end.isoformat() if hasattr(id_period_end, "isoformat") else id_period_end,
                }.items()
                if v
            }
        entry["identifier"] = identifier

    return entry or None


def payload_family_member_history_identifier(
    i: FamilyMemberHistoryIdentifierInput,
) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = i.use.value if hasattr(i.use, "value") else str(i.use)
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value

    type_dict = payload_family_member_history_codeable_concept(i.type)
    if type_dict:
        entry["type"] = type_dict

    if i.period_start or i.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": i.period_start.isoformat() if hasattr(i.period_start, "isoformat") else i.period_start,
                "end": i.period_end.isoformat() if hasattr(i.period_end, "isoformat") else i.period_end,
            }.items()
            if v
        }

    assigner = _reference_with_identifier_from_payload(i, "assigner")
    if assigner:
        entry["assigner"] = assigner

    return entry


def payload_family_member_history_note(n: FamilyMemberHistoryNoteInput) -> dict:
    note_dict: dict = {}
    author_ref = _reference_with_identifier_from_payload(n, "author")
    if author_ref:
        note_dict["authorReference"] = author_ref
    elif n.author_string:
        note_dict["authorString"] = n.author_string

    if n.time:
        note_dict["time"] = n.time.isoformat() if hasattr(n.time, "isoformat") else n.time
    if n.text:
        note_dict["text"] = n.text
    return note_dict


def payload_family_member_history_reason_code(
    rc: FamilyMemberHistoryReasonCodeInput,
) -> dict | None:
    return payload_family_member_history_codeable_concept(rc)


def payload_family_member_history_reason_reference(
    rr: FamilyMemberHistoryReasonReferenceInput,
) -> dict | None:
    return _reference_with_identifier_from_payload(rr, "reference")


def _condition_onset_choice_from_payload(c: Any) -> tuple[str, any] | None:
    onset_age_val = getattr(c, "onset_age_value", None)
    if onset_age_val is not None:
        comp = getattr(c, "onset_age_comparator", None)
        comp_str = comp.value if hasattr(comp, "value") else str(comp) if comp else None
        q = {
            k: v
            for k, v in {
                "value": float(onset_age_val),
                "comparator": _COMPARATOR_SYMBOLS.get(comp_str, comp_str),
                "unit": getattr(c, "onset_age_unit", None),
                "system": getattr(c, "onset_age_system", None),
                "code": getattr(c, "onset_age_code", None),
            }.items()
            if v is not None
        }
        return "onsetAge", q

    low_val = getattr(c, "onset_range_low_value", None)
    high_val = getattr(c, "onset_range_high_value", None)
    if low_val is not None or high_val is not None:
        rng: dict = {}
        if low_val is not None:
            rng["low"] = {
                k: v
                for k, v in {
                    "value": float(low_val),
                    "unit": getattr(c, "onset_range_low_unit", None),
                    "system": getattr(c, "onset_range_low_system", None),
                    "code": getattr(c, "onset_range_low_code", None),
                }.items()
                if v is not None
            }
        if high_val is not None:
            rng["high"] = {
                k: v
                for k, v in {
                    "value": float(high_val),
                    "unit": getattr(c, "onset_range_high_unit", None),
                    "system": getattr(c, "onset_range_high_system", None),
                    "code": getattr(c, "onset_range_high_code", None),
                }.items()
                if v is not None
            }
        return "onsetRange", rng

    p_start = getattr(c, "onset_period_start", None)
    p_end = getattr(c, "onset_period_end", None)
    if p_start or p_end:
        period = {
            k: v
            for k, v in {
                "start": p_start.isoformat() if hasattr(p_start, "isoformat") else p_start,
                "end": p_end.isoformat() if hasattr(p_end, "isoformat") else p_end,
            }.items()
            if v
        }
        return "onsetPeriod", period

    onset_str = getattr(c, "onset_string", None)
    if onset_str:
        return "onsetString", onset_str

    return None


def payload_family_member_history_condition(
    c: FamilyMemberHistoryConditionInput,
) -> dict:
    res: dict = {}
    code_cc = payload_family_member_history_codeable_concept(c.code)
    if code_cc:
        res["code"] = code_cc

    outcome_cc = payload_family_member_history_codeable_concept(c.outcome)
    if outcome_cc:
        res["outcome"] = outcome_cc

    if c.contributed_to_death is not None:
        res["contributedToDeath"] = c.contributed_to_death

    onset = _condition_onset_choice_from_payload(c)
    if onset:
        res[onset[0]] = onset[1]

    if c.note:
        notes = [payload_family_member_history_note(n) for n in c.note]
        notes = [n for n in notes if n]
        if notes:
            res["note"] = notes

    return res


def _born_choice_from_payload(p: Any) -> tuple[str, any] | None:
    p_start = getattr(p, "born_period_start", None)
    p_end = getattr(p, "born_period_end", None)
    if p_start or p_end:
        return "bornPeriod", {
            k: v
            for k, v in {
                "start": p_start.isoformat() if hasattr(p_start, "isoformat") else p_start,
                "end": p_end.isoformat() if hasattr(p_end, "isoformat") else p_end,
            }.items()
            if v
        }
    b_date = getattr(p, "born_date", None)
    if b_date:
        return "bornDate", b_date.isoformat() if hasattr(b_date, "isoformat") else str(b_date)
    b_str = getattr(p, "born_string", None)
    if b_str:
        return "bornString", b_str
    return None


def _age_choice_from_payload(p: Any) -> tuple[str, any] | None:
    age_val = getattr(p, "age_age_value", None)
    if age_val is not None:
        comp = getattr(p, "age_age_comparator", None)
        comp_str = comp.value if hasattr(comp, "value") else str(comp) if comp else None
        q = {
            k: v
            for k, v in {
                "value": float(age_val),
                "comparator": _COMPARATOR_SYMBOLS.get(comp_str, comp_str),
                "unit": getattr(p, "age_age_unit", None),
                "system": getattr(p, "age_age_system", None),
                "code": getattr(p, "age_age_code", None),
            }.items()
            if v is not None
        }
        return "ageAge", q

    low_val = getattr(p, "age_range_low_value", None)
    high_val = getattr(p, "age_range_high_value", None)
    if low_val is not None or high_val is not None:
        rng: dict = {}
        if low_val is not None:
            rng["low"] = {
                k: v
                for k, v in {
                    "value": float(low_val),
                    "unit": getattr(p, "age_range_low_unit", None),
                    "system": getattr(p, "age_range_low_system", None),
                    "code": getattr(p, "age_range_low_code", None),
                }.items()
                if v is not None
            }
        if high_val is not None:
            rng["high"] = {
                k: v
                for k, v in {
                    "value": float(high_val),
                    "unit": getattr(p, "age_range_high_unit", None),
                    "system": getattr(p, "age_range_high_system", None),
                    "code": getattr(p, "age_range_high_code", None),
                }.items()
                if v is not None
            }
        return "ageRange", rng

    age_str = getattr(p, "age_string", None)
    if age_str:
        return "ageString", age_str

    return None


def _deceased_choice_from_payload(p: Any) -> tuple[str, any] | None:
    dec_bool = getattr(p, "deceased_boolean", None)
    if dec_bool is not None:
        return "deceasedBoolean", dec_bool

    age_val = getattr(p, "deceased_age_value", None)
    if age_val is not None:
        comp = getattr(p, "deceased_age_comparator", None)
        comp_str = comp.value if hasattr(comp, "value") else str(comp) if comp else None
        q = {
            k: v
            for k, v in {
                "value": float(age_val),
                "comparator": _COMPARATOR_SYMBOLS.get(comp_str, comp_str),
                "unit": getattr(p, "deceased_age_unit", None),
                "system": getattr(p, "deceased_age_system", None),
                "code": getattr(p, "deceased_age_code", None),
            }.items()
            if v is not None
        }
        return "deceasedAge", q

    low_val = getattr(p, "deceased_range_low_value", None)
    high_val = getattr(p, "deceased_range_high_value", None)
    if low_val is not None or high_val is not None:
        rng: dict = {}
        if low_val is not None:
            rng["low"] = {
                k: v
                for k, v in {
                    "value": float(low_val),
                    "unit": getattr(p, "deceased_range_low_unit", None),
                    "system": getattr(p, "deceased_range_low_system", None),
                    "code": getattr(p, "deceased_range_low_code", None),
                }.items()
                if v is not None
            }
        if high_val is not None:
            rng["high"] = {
                k: v
                for k, v in {
                    "value": float(high_val),
                    "unit": getattr(p, "deceased_range_high_unit", None),
                    "system": getattr(p, "deceased_range_high_system", None),
                    "code": getattr(p, "deceased_range_high_code", None),
                }.items()
                if v is not None
            }
        return "deceasedRange", rng

    dec_date = getattr(p, "deceased_date", None)
    if dec_date:
        return "deceasedDate", dec_date.isoformat() if hasattr(dec_date, "isoformat") else str(dec_date)

    dec_str = getattr(p, "deceased_string", None)
    if dec_str:
        return "deceasedString", dec_str

    return None


def payload_to_fhir_family_member_history(
    payload: FamilyMemberHistoryCreateSchema,
) -> dict:
    """Convert FamilyMemberHistoryCreateSchema to complete FHIR R4 dict for pre-write validation."""
    result: dict = {
        "resourceType": "FamilyMemberHistory",
    }

    if payload.instantiates_canonical:
        result["instantiatesCanonical"] = list(payload.instantiates_canonical)
    if payload.instantiates_uri:
        result["instantiatesUri"] = list(payload.instantiates_uri)

    if payload.status:
        result["status"] = (
            payload.status.value if hasattr(payload.status, "value") else str(payload.status)
        )

    if payload.data_absent_reason:
        dar = payload_family_member_history_codeable_concept(payload.data_absent_reason)
        if dar:
            result["dataAbsentReason"] = dar

    patient = _reference_with_identifier_from_payload(payload, "patient")
    if patient:
        result["patient"] = patient

    if payload.date:
        result["date"] = (
            payload.date.isoformat() if hasattr(payload.date, "isoformat") else str(payload.date)
        )
    if payload.name:
        result["name"] = payload.name

    if payload.relationship:
        rel = payload_family_member_history_codeable_concept(payload.relationship)
        if rel:
            result["relationship"] = rel

    if payload.sex:
        sex = payload_family_member_history_codeable_concept(payload.sex)
        if sex:
            result["sex"] = sex

    born = _born_choice_from_payload(payload)
    if born:
        result[born[0]] = born[1]

    age = _age_choice_from_payload(payload)
    if age:
        result[age[0]] = age[1]

    if payload.estimated_age is not None:
        result["estimatedAge"] = payload.estimated_age

    deceased = _deceased_choice_from_payload(payload)
    if deceased:
        result[deceased[0]] = deceased[1]

    if payload.reason_code:
        rc_list = [
            payload_family_member_history_reason_code(rc)
            for rc in payload.reason_code
        ]
        rc_list = [rc for rc in rc_list if rc]
        if rc_list:
            result["reasonCode"] = rc_list

    if payload.reason_reference:
        rr_list = [
            payload_family_member_history_reason_reference(rr)
            for rr in payload.reason_reference
        ]
        rr_list = [rr for rr in rr_list if rr]
        if rr_list:
            result["reasonReference"] = rr_list

    if payload.note:
        notes = [payload_family_member_history_note(n) for n in payload.note]
        notes = [n for n in notes if n]
        if notes:
            result["note"] = notes

    if payload.condition:
        conds = [
            payload_family_member_history_condition(c) for c in payload.condition
        ]
        conds = [c for c in conds if c]
        if conds:
            result["condition"] = conds

    if payload.identifier:
        ids = [
            payload_family_member_history_identifier(i)
            for i in payload.identifier
        ]
        ids = [i for i in ids if i]
        if ids:
            result["identifier"] = ids

    if payload.extension:
        result["extension"] = list(payload.extension)

    return result


def patch_fragment_to_fhir_family_member_history(
    payload: FamilyMemberHistoryPatchSchema,
) -> tuple[dict, set[str]]:
    """Convert FamilyMemberHistoryPatchSchema to (fhir_fragment, touched_keys) for pre-write validation."""
    provided = payload.model_fields_set
    fragment: dict = {}
    touched: set[str] = set()

    if "instantiates_canonical" in provided:
        touched.add("instantiatesCanonical")
        if payload.instantiates_canonical is not None:
            fragment["instantiatesCanonical"] = list(payload.instantiates_canonical)

    if "instantiates_uri" in provided:
        touched.add("instantiatesUri")
        if payload.instantiates_uri is not None:
            fragment["instantiatesUri"] = list(payload.instantiates_uri)

    if "status" in provided:
        touched.add("status")
        if payload.status is not None:
            fragment["status"] = (
                payload.status.value if hasattr(payload.status, "value") else str(payload.status)
            )

    if "data_absent_reason" in provided:
        touched.add("dataAbsentReason")
        if payload.data_absent_reason is not None:
            dar = payload_family_member_history_codeable_concept(payload.data_absent_reason)
            if dar:
                fragment["dataAbsentReason"] = dar

    if provided & _PATIENT_FIELDS:
        touched.add("patient")
        patient = _reference_with_identifier_from_payload(payload, "patient")
        if patient:
            fragment["patient"] = patient

    if "date" in provided:
        touched.add("date")
        if payload.date is not None:
            fragment["date"] = (
                payload.date.isoformat() if hasattr(payload.date, "isoformat") else str(payload.date)
            )

    if "name" in provided:
        touched.add("name")
        if payload.name is not None:
            fragment["name"] = payload.name

    if "relationship" in provided:
        touched.add("relationship")
        if payload.relationship is not None:
            rel = payload_family_member_history_codeable_concept(payload.relationship)
            if rel:
                fragment["relationship"] = rel

    if "sex" in provided:
        touched.add("sex")
        if payload.sex is not None:
            sex = payload_family_member_history_codeable_concept(payload.sex)
            if sex:
                fragment["sex"] = sex

    if provided & _BORN_FIELDS:
        touched.update(_BORN_FHIR_KEYS)
        born = _born_choice_from_payload(payload)
        if born:
            fragment[born[0]] = born[1]

    if provided & _AGE_FIELDS:
        touched.update(_AGE_FHIR_KEYS)
        age = _age_choice_from_payload(payload)
        if age:
            fragment[age[0]] = age[1]

    if "estimated_age" in provided:
        touched.add("estimatedAge")
        if payload.estimated_age is not None:
            fragment["estimatedAge"] = payload.estimated_age

    if provided & _DECEASED_FIELDS:
        touched.update(_DECEASED_FHIR_KEYS)
        deceased = _deceased_choice_from_payload(payload)
        if deceased:
            fragment[deceased[0]] = deceased[1]

    if "reason_code" in provided:
        touched.add("reasonCode")
        if payload.reason_code is not None:
            rc_list = [
                payload_family_member_history_reason_code(rc)
                for rc in payload.reason_code
            ]
            rc_list = [rc for rc in rc_list if rc]
            if rc_list:
                fragment["reasonCode"] = rc_list

    if "reason_reference" in provided:
        touched.add("reasonReference")
        if payload.reason_reference is not None:
            rr_list = [
                payload_family_member_history_reason_reference(rr)
                for rr in payload.reason_reference
            ]
            rr_list = [rr for rr in rr_list if rr]
            if rr_list:
                fragment["reasonReference"] = rr_list

    if "note" in provided:
        touched.add("note")
        if payload.note is not None:
            notes = [payload_family_member_history_note(n) for n in payload.note]
            notes = [n for n in notes if n]
            if notes:
                fragment["note"] = notes

    if "condition" in provided:
        touched.add("condition")
        if payload.condition is not None:
            conds = [
                payload_family_member_history_condition(c) for c in payload.condition
            ]
            conds = [c for c in conds if c]
            if conds:
                fragment["condition"] = conds

    if "identifier" in provided:
        touched.add("identifier")
        if payload.identifier is not None:
            ids = [
                payload_family_member_history_identifier(i)
                for i in payload.identifier
            ]
            ids = [i for i in ids if i]
            if ids:
                fragment["identifier"] = ids

    if "extension" in provided:
        touched.add("extension")
        if payload.extension is not None:
            fragment["extension"] = list(payload.extension)

    return fragment, touched
