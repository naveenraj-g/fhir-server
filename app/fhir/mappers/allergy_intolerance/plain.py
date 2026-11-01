from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.allergy_intolerance import (
        AllergyIntoleranceIdentifier,
        AllergyIntoleranceModel,
        AllergyIntoleranceNote,
        AllergyIntoleranceReaction,
        AllergyIntoleranceReactionNote,
    )


def _plain_ref(ref_raw: str | None, ref_type: Any, ref_id: int | None) -> str | None:
    if ref_raw:
        return ref_raw
    if ref_type and ref_id:
        return f"{fhir_enum(ref_type)}/{ref_id}"
    return None


def _format_dt(v: Any) -> str | None:
    if v is None:
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return str(v)


def _plain_identifier_fallback(obj, prefix: str) -> dict:
    return {
        f"{prefix}_identifier_use": (
            fhir_enum(v) if (v := getattr(obj, f"{prefix}_identifier_use", None)) else None
        ),
        f"{prefix}_identifier_type_system": getattr(obj, f"{prefix}_identifier_type_system", None),
        f"{prefix}_identifier_type_version": getattr(obj, f"{prefix}_identifier_type_version", None),
        f"{prefix}_identifier_type_code": getattr(obj, f"{prefix}_identifier_type_code", None),
        f"{prefix}_identifier_type_display": getattr(obj, f"{prefix}_identifier_type_display", None),
        f"{prefix}_identifier_type_user_selected": getattr(
            obj, f"{prefix}_identifier_type_user_selected", None
        ),
        f"{prefix}_identifier_type_text": getattr(obj, f"{prefix}_identifier_type_text", None),
        f"{prefix}_identifier_system": getattr(obj, f"{prefix}_identifier_system", None),
        f"{prefix}_identifier_value": getattr(obj, f"{prefix}_identifier_value", None),
        f"{prefix}_identifier_period_start": _format_dt(
            getattr(obj, f"{prefix}_identifier_period_start", None)
        ),
        f"{prefix}_identifier_period_end": _format_dt(
            getattr(obj, f"{prefix}_identifier_period_end", None)
        ),
    }


def _plain_codeable_concept(codings, text: str | None) -> dict | None:
    c_list = [
        {
            "id": getattr(c, "id", None),
            "system": c.system,
            "version": c.version,
            "code": c.code,
            "display": c.display,
            "user_selected": c.user_selected,
        }
        for c in codings or []
    ]
    if not c_list and not text:
        return None
    res: dict = {}
    if text:
        res["text"] = text
    if c_list:
        res["coding"] = c_list
    return res


def _plain_identifier(i: AllergyIntoleranceIdentifier) -> dict:
    type_obj = None
    if i.type_text or getattr(i, "type_codings", None):
        type_obj = {
            "text": i.type_text,
            "coding": [
                {
                    "system": c.system,
                    "version": c.version,
                    "code": c.code,
                    "display": c.display,
                    "user_selected": c.user_selected,
                }
                for c in getattr(i, "type_codings", None) or []
            ]
            or None,
        }
    return {
        "id": i.id,
        "use": fhir_enum(i.use) if i.use else None,
        "type": type_obj,
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start,
        "period_end": i.period_end,
        "assigner": _plain_ref(i.assigner_reference, i.assigner_type, i.assigner_id),
        "assigner_display": i.assigner_display,
        **_plain_identifier_fallback(i, "assigner"),
    }


def _plain_annotation(
    note: AllergyIntoleranceNote | AllergyIntoleranceReactionNote,
) -> dict:
    return {
        "id": note.id,
        "text": note.text,
        "time": note.time,
        "author_string": getattr(note, "author_string", None),
        "author_reference": _plain_ref(
            getattr(note, "author_reference", None),
            getattr(note, "author_reference_type", None),
            getattr(note, "author_reference_id", None),
        ),
        "author_reference_type": (
            fhir_enum(v) if (v := getattr(note, "author_reference_type", None)) else None
        ),
        "author_reference_id": getattr(note, "author_reference_id", None),
        "author_reference_display": getattr(note, "author_reference_display", None),
        **_plain_identifier_fallback(note, "author_reference"),
    }


def _plain_reaction(r: AllergyIntoleranceReaction) -> dict:
    substance_obj = _plain_codeable_concept(
        getattr(r, "substance_codings", None), r.substance_text
    )
    manifestations = []
    for m in getattr(r, "manifestations", None) or []:
        m_obj = _plain_codeable_concept(getattr(m, "codings", None), m.text)
        if m_obj:
            manifestations.append(m_obj)

    exposure_route_obj = _plain_codeable_concept(
        getattr(r, "exposure_route_codings", None), r.exposure_route_text
    )
    notes = [
        _plain_annotation(n) for n in (getattr(r, "notes", None) or [])
    ]
    return {
        "id": r.id,
        "substance": substance_obj,
        "manifestation": manifestations,
        "description": r.description,
        "onset": r.onset,
        "severity": fhir_enum(r.severity) if r.severity else None,
        "exposure_route": exposure_route_obj,
        "note": notes or None,
    }


def to_plain_allergy_intolerance(model: AllergyIntoleranceModel) -> dict:
    """Map AllergyIntoleranceModel ORM instance to plain snake_case response dict."""
    return {
        "id": model.allergy_intolerance_id,
        "clinical_status": _plain_codeable_concept(
            getattr(model, "clinical_status_codings", None),
            model.clinical_status_text,
        ),
        "verification_status": _plain_codeable_concept(
            getattr(model, "verification_status_codings", None),
            model.verification_status_text,
        ),
        "type": fhir_enum(model.type) if model.type else None,
        "category": [fhir_enum(c) for c in model.category] if model.category else None,
        "criticality": fhir_enum(model.criticality) if model.criticality else None,
        "code": _plain_codeable_concept(
            getattr(model, "code_codings", None),
            model.code_text,
        ),
        "patient": _plain_ref(
            model.patient_reference,
            model.patient_type,
            model.patient_id,
        )
        or model.patient_reference,
        "patient_display": model.patient_display,
        **_plain_identifier_fallback(model, "patient"),
        "encounter": _plain_ref(
            model.encounter_reference,
            model.encounter_type,
            model.encounter_id,
        ),
        "encounter_display": model.encounter_display,
        **_plain_identifier_fallback(model, "encounter"),
        "onset_date_time": model.onset_date_time,
        "onset_age": model.onset_age,
        "onset_period_start": model.onset_period_start,
        "onset_period_end": model.onset_period_end,
        "onset_range": model.onset_range,
        "onset_string": model.onset_string,
        "recorded_date": model.recorded_date,
        "recorder": _plain_ref(
            model.recorder_reference,
            model.recorder_type,
            model.recorder_id,
        ),
        "recorder_display": model.recorder_display,
        **_plain_identifier_fallback(model, "recorder"),
        "asserter": _plain_ref(
            model.asserter_reference,
            model.asserter_type,
            model.asserter_id,
        ),
        "asserter_display": model.asserter_display,
        **_plain_identifier_fallback(model, "asserter"),
        "last_occurrence": model.last_occurrence,
        "note": [
            _plain_annotation(n) for n in (getattr(model, "notes", None) or [])
        ]
        or None,
        "reaction": [
            _plain_reaction(r) for r in (getattr(model, "reactions", None) or [])
        ]
        or None,
        "identifier": [
            _plain_identifier(i) for i in (getattr(model, "identifiers", None) or [])
        ]
        or None,
        "extension": model.extension or [],
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }
