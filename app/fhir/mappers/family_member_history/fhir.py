from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.family_member_history import FamilyMemberHistoryModel

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


def fhir_family_member_history_codeable_concept(codings, text: str | None) -> dict | None:
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
                if v
            }
        entry["identifier"] = identifier

    return entry


def _fhir_quantity(obj, prefix: str) -> dict | None:
    value = getattr(obj, f"{prefix}_value", None)
    if value is None:
        return None
    comparator = getattr(obj, f"{prefix}_comparator", None)
    result = {
        k: v
        for k, v in {
            "value": float(value),
            "comparator": _COMPARATOR_SYMBOLS.get(fhir_enum(comparator)) if comparator else None,
            "unit": getattr(obj, f"{prefix}_unit", None),
            "system": getattr(obj, f"{prefix}_system", None),
            "code": getattr(obj, f"{prefix}_code", None),
        }.items()
        if v is not None
    }
    return result or None


def _fhir_range(obj, prefix: str) -> dict | None:
    low_val = getattr(obj, f"{prefix}_low_value", None)
    high_val = getattr(obj, f"{prefix}_high_value", None)
    if low_val is None and high_val is None:
        return None

    result: dict = {}
    if low_val is not None:
        result["low"] = {
            k: v
            for k, v in {
                "value": float(low_val),
                "unit": getattr(obj, f"{prefix}_low_unit", None),
                "system": getattr(obj, f"{prefix}_low_system", None),
                "code": getattr(obj, f"{prefix}_low_code", None),
            }.items()
            if v is not None
        }
    if high_val is not None:
        result["high"] = {
            k: v
            for k, v in {
                "value": float(high_val),
                "unit": getattr(obj, f"{prefix}_high_unit", None),
                "system": getattr(obj, f"{prefix}_high_system", None),
                "code": getattr(obj, f"{prefix}_high_code", None),
            }.items()
            if v is not None
        }
    return result or None


def fhir_family_member_history_identifier(i) -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value

    type_codings = _fhir_coding_list(i.type_codings)
    if type_codings or i.type_text:
        type_cc: dict = {}
        if type_codings:
            type_cc["coding"] = type_codings
        if i.type_text:
            type_cc["text"] = i.type_text
        entry["type"] = type_cc

    if i.period_start or i.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(i.period_start) if i.period_start else None,
                "end": fhir_instant(i.period_end) if i.period_end else None,
            }.items()
            if v
        }

    assigner = _fhir_reference_with_identifier_fallback(i, "assigner")
    if assigner:
        entry["assigner"] = assigner

    return entry


def fhir_family_member_history_note(n) -> dict:
    note_dict: dict = {}
    author_ref = _fhir_reference_with_identifier_fallback(n, "author")
    if author_ref:
        note_dict["authorReference"] = author_ref
    elif n.author_string:
        note_dict["authorString"] = n.author_string

    if n.time:
        note_dict["time"] = fhir_instant(n.time)
    if n.text:
        note_dict["text"] = n.text
    return note_dict


def fhir_family_member_history_condition(c) -> dict:
    res: dict = {}
    code_cc = fhir_family_member_history_codeable_concept(c.code_codings, c.code_text)
    if code_cc:
        res["code"] = code_cc

    outcome_cc = fhir_family_member_history_codeable_concept(c.outcome_codings, c.outcome_text)
    if outcome_cc:
        res["outcome"] = outcome_cc

    if c.contributed_to_death is not None:
        res["contributedToDeath"] = c.contributed_to_death

    # onset[x] (Age | Range | Period | string)
    if c.onset_age_value is not None:
        age_dict = _fhir_quantity(c, "onset_age")
        if age_dict:
            res["onsetAge"] = age_dict
    elif c.onset_range_low_value is not None or c.onset_range_high_value is not None:
        range_dict = _fhir_range(c, "onset_range")
        if range_dict:
            res["onsetRange"] = range_dict
    elif c.onset_period_start or c.onset_period_end:
        res["onsetPeriod"] = {
            k: v
            for k, v in {
                "start": fhir_instant(c.onset_period_start) if c.onset_period_start else None,
                "end": fhir_instant(c.onset_period_end) if c.onset_period_end else None,
            }.items()
            if v
        }
    elif c.onset_string:
        res["onsetString"] = c.onset_string

    notes = [fhir_family_member_history_note(n) for n in (c.notes or [])]
    notes = [n for n in notes if n]
    if notes:
        res["note"] = notes

    return res


def _fhir_meta(model: FamilyMemberHistoryModel) -> dict:
    meta: dict = {}
    if model.updated_at:
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    extensions = []
    if model.tenant_id:
        extensions.append({"url": f"{_EXT_BASE}/tenant-id", "valueString": model.tenant_id})
    if model.created_by:
        extensions.append({"url": f"{_EXT_BASE}/created-by", "valueString": model.created_by})
    if model.updated_by:
        extensions.append({"url": f"{_EXT_BASE}/updated-by", "valueString": model.updated_by})
    if model.created_at:
        extensions.append({"url": f"{_EXT_BASE}/created-at", "valueInstant": fhir_instant(model.created_at)})
    if extensions:
        meta["extension"] = extensions
    return meta


def to_fhir_family_member_history(model: FamilyMemberHistoryModel) -> dict:
    """Build a complete FHIR R4 FamilyMemberHistory resource representation."""
    meta = _fhir_meta(model)

    res: dict = {
        "resourceType": "FamilyMemberHistory",
        "id": str(model.family_member_history_id),
    }
    if meta:
        res["meta"] = meta

    if model.instantiates_canonical:
        res["instantiatesCanonical"] = list(model.instantiates_canonical)
    if model.instantiates_uri:
        res["instantiatesUri"] = list(model.instantiates_uri)

    res["status"] = fhir_enum(model.status)

    data_absent = fhir_family_member_history_codeable_concept(
        model.data_absent_reason_codings, model.data_absent_reason_text
    )
    if data_absent:
        res["dataAbsentReason"] = data_absent

    res["patient"] = _fhir_reference_with_identifier_fallback(model, "patient")

    if model.date:
        res["date"] = fhir_instant(model.date)
    if model.name:
        res["name"] = model.name

    rel = fhir_family_member_history_codeable_concept(
        model.relationship_codings, model.relationship_text
    )
    if rel:
        res["relationship"] = rel

    sex = fhir_family_member_history_codeable_concept(
        model.sex_codings, model.sex_text
    )
    if sex:
        res["sex"] = sex

    # born[x] (Period | date | string)
    if model.born_period_start or model.born_period_end:
        res["bornPeriod"] = {
            k: v
            for k, v in {
                "start": fhir_instant(model.born_period_start) if model.born_period_start else None,
                "end": fhir_instant(model.born_period_end) if model.born_period_end else None,
            }.items()
            if v
        }
    elif model.born_date:
        res["bornDate"] = model.born_date.isoformat()
    elif model.born_string:
        res["bornString"] = model.born_string

    # age[x] (Age | Range | string)
    if model.age_age_value is not None:
        age_dict = _fhir_quantity(model, "age_age")
        if age_dict:
            res["ageAge"] = age_dict
    elif model.age_range_low_value is not None or model.age_range_high_value is not None:
        range_dict = _fhir_range(model, "age_range")
        if range_dict:
            res["ageRange"] = range_dict
    elif model.age_string:
        res["ageString"] = model.age_string

    if model.estimated_age is not None:
        res["estimatedAge"] = model.estimated_age

    # deceased[x] (boolean | Age | Range | date | string)
    if model.deceased_boolean is not None:
        res["deceasedBoolean"] = model.deceased_boolean
    elif model.deceased_age_value is not None:
        dec_age = _fhir_quantity(model, "deceased_age")
        if dec_age:
            res["deceasedAge"] = dec_age
    elif model.deceased_range_low_value is not None or model.deceased_range_high_value is not None:
        dec_range = _fhir_range(model, "deceased_range")
        if dec_range:
            res["deceasedRange"] = dec_range
    elif model.deceased_date:
        res["deceasedDate"] = model.deceased_date.isoformat()
    elif model.deceased_string:
        res["deceasedString"] = model.deceased_string

    # reasonCode
    rc_list = [
        fhir_family_member_history_codeable_concept(rc.codings, rc.text)
        for rc in (model.reason_codes or [])
    ]
    rc_list = [rc for rc in rc_list if rc]
    if rc_list:
        res["reasonCode"] = rc_list

    # reasonReference
    rr_list = [
        _fhir_reference_with_identifier_fallback(rr, "reference")
        for rr in (model.reason_references or [])
    ]
    rr_list = [rr for rr in rr_list if rr]
    if rr_list:
        res["reasonReference"] = rr_list

    # note
    notes = [fhir_family_member_history_note(n) for n in (model.notes or [])]
    notes = [n for n in notes if n]
    if notes:
        res["note"] = notes

    # condition
    conditions = [
        fhir_family_member_history_condition(c) for c in (model.conditions or [])
    ]
    conditions = [c for c in conditions if c]
    if conditions:
        res["condition"] = conditions

    # identifier
    identifiers = [
        fhir_family_member_history_identifier(i) for i in (model.identifiers or [])
    ]
    identifiers = [i for i in identifiers if i]
    if identifiers:
        res["identifier"] = identifiers

    if model.extension:
        res["extension"] = list(model.extension)

    return {k: v for k, v in res.items() if v is not None}
