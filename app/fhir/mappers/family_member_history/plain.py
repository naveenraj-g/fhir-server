from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.family_member_history import (
        FamilyMemberHistoryCondition,
        FamilyMemberHistoryIdentifier,
        FamilyMemberHistoryModel,
        FamilyMemberHistoryNote,
        FamilyMemberHistoryReasonCode,
        FamilyMemberHistoryReasonReference,
    )


def _plain_coding_list(codings) -> list[dict]:
    result = []
    for c in codings or []:
        entry = {
            "id": c.id,
            "system": c.system,
            "version": c.version,
            "code": c.code,
            "display": c.display,
            "user_selected": c.user_selected,
        }
        result.append({k: v for k, v in entry.items() if v is not None})
    return result


def plain_family_member_history_codeable_concept(
    codings, text: str | None
) -> dict | None:
    coding_list = _plain_coding_list(codings)
    if not coding_list and not text:
        return None
    res: dict = {}
    if coding_list:
        res["coding"] = coding_list
    if text:
        res["text"] = text
    return res


def plain_family_member_history_identifier(
    i: FamilyMemberHistoryIdentifier,
) -> dict:
    assigner_ref = None
    if i.assigner_reference:
        assigner_ref = i.assigner_reference
    elif i.assigner_type and i.assigner_id:
        assigner_ref = f"{fhir_enum(i.assigner_type)}/{i.assigner_id}"

    return {
        "id": i.id,
        "use": fhir_enum(i.use) if i.use else None,
        "type": plain_family_member_history_codeable_concept(
            i.type_codings, i.type_text
        ),
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start,
        "period_end": i.period_end,
        "assigner": assigner_ref,
        "assigner_display": i.assigner_display,
        "assigner_identifier_use": (
            fhir_enum(i.assigner_identifier_use)
            if i.assigner_identifier_use
            else None
        ),
        "assigner_identifier_type_system": i.assigner_identifier_type_system,
        "assigner_identifier_type_version": i.assigner_identifier_type_version,
        "assigner_identifier_type_code": i.assigner_identifier_type_code,
        "assigner_identifier_type_display": i.assigner_identifier_type_display,
        "assigner_identifier_type_user_selected": i.assigner_identifier_type_user_selected,
        "assigner_identifier_type_text": i.assigner_identifier_type_text,
        "assigner_identifier_system": i.assigner_identifier_system,
        "assigner_identifier_value": i.assigner_identifier_value,
        "assigner_identifier_period_start": i.assigner_identifier_period_start,
        "assigner_identifier_period_end": i.assigner_identifier_period_end,
    }


def plain_family_member_history_note(n: FamilyMemberHistoryNote) -> dict:
    author_ref = None
    if n.author_reference:
        author_ref = n.author_reference
    elif n.author_type and n.author_id:
        author_ref = f"{fhir_enum(n.author_type)}/{n.author_id}"

    return {
        "id": n.id,
        "author_string": n.author_string,
        "author_reference": author_ref,
        "author_reference_display": n.author_display,
        "author_identifier_use": (
            fhir_enum(n.author_identifier_use)
            if n.author_identifier_use
            else None
        ),
        "author_identifier_type_system": n.author_identifier_type_system,
        "author_identifier_type_version": n.author_identifier_type_version,
        "author_identifier_type_code": n.author_identifier_type_code,
        "author_identifier_type_display": n.author_identifier_type_display,
        "author_identifier_type_user_selected": n.author_identifier_type_user_selected,
        "author_identifier_type_text": n.author_identifier_type_text,
        "author_identifier_system": n.author_identifier_system,
        "author_identifier_value": n.author_identifier_value,
        "author_identifier_period_start": n.author_identifier_period_start,
        "author_identifier_period_end": n.author_identifier_period_end,
        "time": n.time,
        "text": n.text,
    }


def plain_family_member_history_reason_code(
    rc: FamilyMemberHistoryReasonCode,
) -> dict:
    return {
        "id": rc.id,
        "coding": _plain_coding_list(rc.codings),
        "text": rc.text,
    }


def plain_family_member_history_reason_reference(
    rr: FamilyMemberHistoryReasonReference,
) -> dict:
    ref = None
    if rr.reference_reference:
        ref = rr.reference_reference
    elif rr.reference_type and rr.reference_id:
        ref = f"{fhir_enum(rr.reference_type)}/{rr.reference_id}"

    return {
        "id": rr.id,
        "reference": ref,
        "display": rr.reference_display,
        "identifier_use": (
            fhir_enum(rr.reference_identifier_use)
            if rr.reference_identifier_use
            else None
        ),
        "identifier_type_system": rr.reference_identifier_type_system,
        "identifier_type_version": rr.reference_identifier_type_version,
        "identifier_type_code": rr.reference_identifier_type_code,
        "identifier_type_display": rr.reference_identifier_type_display,
        "identifier_type_user_selected": rr.reference_identifier_type_user_selected,
        "identifier_type_text": rr.reference_identifier_type_text,
        "identifier_system": rr.reference_identifier_system,
        "identifier_value": rr.reference_identifier_value,
        "identifier_period_start": rr.reference_identifier_period_start,
        "identifier_period_end": rr.reference_identifier_period_end,
    }


def plain_family_member_history_condition(
    c: FamilyMemberHistoryCondition,
) -> dict:
    return {
        "id": c.id,
        "code": plain_family_member_history_codeable_concept(
            c.code_codings, c.code_text
        ),
        "outcome": plain_family_member_history_codeable_concept(
            c.outcome_codings, c.outcome_text
        ),
        "contributed_to_death": c.contributed_to_death,
        "onset_age_value": float(c.onset_age_value) if c.onset_age_value is not None else None,
        "onset_age_comparator": fhir_enum(c.onset_age_comparator) if c.onset_age_comparator else None,
        "onset_age_unit": c.onset_age_unit,
        "onset_age_system": c.onset_age_system,
        "onset_age_code": c.onset_age_code,
        "onset_range_low_value": float(c.onset_range_low_value) if c.onset_range_low_value is not None else None,
        "onset_range_low_unit": c.onset_range_low_unit,
        "onset_range_low_system": c.onset_range_low_system,
        "onset_range_low_code": c.onset_range_low_code,
        "onset_range_high_value": float(c.onset_range_high_value) if c.onset_range_high_value is not None else None,
        "onset_range_high_unit": c.onset_range_high_unit,
        "onset_range_high_system": c.onset_range_high_system,
        "onset_range_high_code": c.onset_range_high_code,
        "onset_period_start": c.onset_period_start,
        "onset_period_end": c.onset_period_end,
        "onset_string": c.onset_string,
        "note": [plain_family_member_history_note(n) for n in (c.notes or [])],
    }


def to_plain_family_member_history(model: FamilyMemberHistoryModel) -> dict:
    """Build a plain snake_case dict representation of FamilyMemberHistory."""
    pat_ref = None
    if model.patient_reference:
        pat_ref = model.patient_reference
    elif model.patient_type and model.patient_id:
        pat_ref = f"{fhir_enum(model.patient_type)}/{model.patient_id}"

    return {
        "id": model.family_member_history_id,
        "status": fhir_enum(model.status),
        "data_absent_reason": plain_family_member_history_codeable_concept(
            model.data_absent_reason_codings, model.data_absent_reason_text
        ),
        "patient": pat_ref,
        "patient_display": model.patient_display,
        "patient_identifier_use": (
            fhir_enum(model.patient_identifier_use)
            if model.patient_identifier_use
            else None
        ),
        "patient_identifier_type_system": model.patient_identifier_type_system,
        "patient_identifier_type_version": model.patient_identifier_type_version,
        "patient_identifier_type_code": model.patient_identifier_type_code,
        "patient_identifier_type_display": model.patient_identifier_type_display,
        "patient_identifier_type_user_selected": model.patient_identifier_type_user_selected,
        "patient_identifier_type_text": model.patient_identifier_type_text,
        "patient_identifier_system": model.patient_identifier_system,
        "patient_identifier_value": model.patient_identifier_value,
        "patient_identifier_period_start": (
            model.patient_identifier_period_start.isoformat()
            if model.patient_identifier_period_start
            else None
        ),
        "patient_identifier_period_end": (
            model.patient_identifier_period_end.isoformat()
            if model.patient_identifier_period_end
            else None
        ),
        "date": model.date,
        "name": model.name,
        "relationship": plain_family_member_history_codeable_concept(
            model.relationship_codings, model.relationship_text
        ),
        "sex": plain_family_member_history_codeable_concept(
            model.sex_codings, model.sex_text
        ),
        "born_period_start": model.born_period_start,
        "born_period_end": model.born_period_end,
        "born_date": model.born_date,
        "born_string": model.born_string,
        "age_age_value": float(model.age_age_value) if model.age_age_value is not None else None,
        "age_age_comparator": fhir_enum(model.age_age_comparator) if model.age_age_comparator else None,
        "age_age_unit": model.age_age_unit,
        "age_age_system": model.age_age_system,
        "age_age_code": model.age_age_code,
        "age_range_low_value": float(model.age_range_low_value) if model.age_range_low_value is not None else None,
        "age_range_low_unit": model.age_range_low_unit,
        "age_range_low_system": model.age_range_low_system,
        "age_range_low_code": model.age_range_low_code,
        "age_range_high_value": float(model.age_range_high_value) if model.age_range_high_value is not None else None,
        "age_range_high_unit": model.age_range_high_unit,
        "age_range_high_system": model.age_range_high_system,
        "age_range_high_code": model.age_range_high_code,
        "age_string": model.age_string,
        "estimated_age": model.estimated_age,
        "deceased_boolean": model.deceased_boolean,
        "deceased_age_value": float(model.deceased_age_value) if model.deceased_age_value is not None else None,
        "deceased_age_comparator": fhir_enum(model.deceased_age_comparator) if model.deceased_age_comparator else None,
        "deceased_age_unit": model.deceased_age_unit,
        "deceased_age_system": model.deceased_age_system,
        "deceased_age_code": model.deceased_age_code,
        "deceased_range_low_value": float(model.deceased_range_low_value) if model.deceased_range_low_value is not None else None,
        "deceased_range_low_unit": model.deceased_range_low_unit,
        "deceased_range_low_system": model.deceased_range_low_system,
        "deceased_range_low_code": model.deceased_range_low_code,
        "deceased_range_high_value": float(model.deceased_range_high_value) if model.deceased_range_high_value is not None else None,
        "deceased_range_high_unit": model.deceased_range_high_unit,
        "deceased_range_high_system": model.deceased_range_high_system,
        "deceased_range_high_code": model.deceased_range_high_code,
        "deceased_date": model.deceased_date,
        "deceased_string": model.deceased_string,
        "instantiates_canonical": list(model.instantiates_canonical) if model.instantiates_canonical else None,
        "instantiates_uri": list(model.instantiates_uri) if model.instantiates_uri else None,
        "identifier": [plain_family_member_history_identifier(i) for i in (model.identifiers or [])],
        "reason_code": [plain_family_member_history_reason_code(rc) for rc in (model.reason_codes or [])],
        "reason_reference": [plain_family_member_history_reason_reference(rr) for rr in (model.reason_references or [])],
        "note": [plain_family_member_history_note(n) for n in (model.notes or [])],
        "condition": [plain_family_member_history_condition(c) for c in (model.conditions or [])],
        "extension": list(model.extension) if model.extension else [],
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }
