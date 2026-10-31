from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.condition import ConditionModel


def _audit_fields(obj) -> dict:
    return {
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        "created_by": obj.created_by,
        "updated_by": obj.updated_by,
    }


def plain_coding(c) -> dict:
    return {
        "id": c.id,
        "system": c.system,
        "version": c.version,
        "code": c.code,
        "display": c.display,
        "user_selected": c.user_selected,
        **_audit_fields(c),
    }


def _plain_reference(obj, prefix: str) -> dict | None:
    raw_reference = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    if not (raw_reference or ref_type or ref_id or display):
        return None

    return {
        "reference": raw_reference or (f"{fhir_enum(ref_type)}/{ref_id}" if ref_type and ref_id else None),
        "id": ref_id,
        "type": fhir_enum(ref_type) if ref_type else None,
        "display": display,
    }


def plain_condition_identifier(i) -> dict:
    ref_type = i.assigner_type
    ref_id = i.assigner_id
    return {
        "id": i.id,
        "use": fhir_enum(i.use) if i.use else None,
        "type_text": i.type_text,
        "type_codings": [plain_coding(c) for c in (i.type_codings or [])],
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start.isoformat() if i.period_start else None,
        "period_end": i.period_end.isoformat() if i.period_end else None,
        "assigner_reference": i.assigner_reference,
        "assigner_id": ref_id,
        "assigner_type": fhir_enum(ref_type) if ref_type else None,
        "assigner_display": i.assigner_display,
        **_audit_fields(i),
    }


def plain_condition_category(cat) -> dict:
    return {
        "id": cat.id,
        "text": cat.text,
        "codings": [plain_coding(c) for c in (cat.codings or [])],
        **_audit_fields(cat),
    }


def plain_condition_body_site(b) -> dict:
    return {
        "id": b.id,
        "text": b.text,
        "codings": [plain_coding(c) for c in (b.codings or [])],
        **_audit_fields(b),
    }


def plain_condition_stage(s) -> dict:
    return {
        "id": s.id,
        "summary_text": s.summary_text,
        "summary_codings": [plain_coding(c) for c in (s.summary_codings or [])],
        "type_text": s.type_text,
        "type_codings": [plain_coding(c) for c in (s.type_codings or [])],
        "assessments": [
            _plain_reference(a, "reference")
            for a in (s.assessments or [])
            if _plain_reference(a, "reference") is not None
        ],
        **_audit_fields(s),
    }


def plain_condition_evidence_code(c) -> dict:
    return {
        "id": c.id,
        "text": c.text,
        "codings": [plain_coding(coding) for coding in (c.codings or [])],
        **_audit_fields(c),
    }


def plain_condition_evidence(e) -> dict:
    return {
        "id": e.id,
        "codes": [plain_condition_evidence_code(c) for c in (e.codes or [])],
        "details": [
            _plain_reference(d, "reference")
            for d in (e.details or [])
            if _plain_reference(d, "reference") is not None
        ],
        **_audit_fields(e),
    }


def plain_condition_note(n) -> dict:
    author_type = n.author_type
    return {
        "id": n.id,
        "author_string": n.author_string,
        "author_reference": n.author_reference,
        "author_id": n.author_id,
        "author_type": fhir_enum(author_type) if author_type else None,
        "author_display": n.author_display,
        "time": n.time.isoformat() if n.time else None,
        "text": n.text,
        **_audit_fields(n),
    }


def to_plain_condition(cond: ConditionModel) -> dict:
    return {
        "id": cond.condition_id,
        "clinical_status_text": cond.clinical_status_text,
        "clinical_status_codings": [
            plain_coding(c) for c in (cond.clinical_status_codings or [])
        ],
        "verification_status_text": cond.verification_status_text,
        "verification_status_codings": [
            plain_coding(c) for c in (cond.verification_status_codings or [])
        ],
        "severity_text": cond.severity_text,
        "severity_codings": [
            plain_coding(c) for c in (cond.severity_codings or [])
        ],
        "code_text": cond.code_text,
        "code_codings": [
            plain_coding(c) for c in (cond.code_codings or [])
        ],
        "categories": [
            plain_condition_category(cat) for cat in (cond.categories or [])
        ],
        "body_sites": [
            plain_condition_body_site(b) for b in (cond.body_sites or [])
        ],
        "subject": _plain_reference(cond, "subject"),
        "encounter": _plain_reference(cond, "encounter"),
        "onset_date_time": (
            cond.onset_date_time.isoformat() if cond.onset_date_time else None
        ),
        "onset_age_value": (
            float(cond.onset_age_value) if cond.onset_age_value is not None else None
        ),
        "onset_age_comparator": (
            fhir_enum(cond.onset_age_comparator) if cond.onset_age_comparator else None
        ),
        "onset_age_unit": cond.onset_age_unit,
        "onset_age_system": cond.onset_age_system,
        "onset_age_code": cond.onset_age_code,
        "onset_period_start": (
            cond.onset_period_start.isoformat() if cond.onset_period_start else None
        ),
        "onset_period_end": (
            cond.onset_period_end.isoformat() if cond.onset_period_end else None
        ),
        "onset_range_low_value": (
            float(cond.onset_range_low_value) if cond.onset_range_low_value is not None else None
        ),
        "onset_range_low_unit": cond.onset_range_low_unit,
        "onset_range_low_system": cond.onset_range_low_system,
        "onset_range_low_code": cond.onset_range_low_code,
        "onset_range_high_value": (
            float(cond.onset_range_high_value) if cond.onset_range_high_value is not None else None
        ),
        "onset_range_high_unit": cond.onset_range_high_unit,
        "onset_range_high_system": cond.onset_range_high_system,
        "onset_range_high_code": cond.onset_range_high_code,
        "onset_string": cond.onset_string,
        "abatement_date_time": (
            cond.abatement_date_time.isoformat() if cond.abatement_date_time else None
        ),
        "abatement_age_value": (
            float(cond.abatement_age_value) if cond.abatement_age_value is not None else None
        ),
        "abatement_age_comparator": (
            fhir_enum(cond.abatement_age_comparator) if cond.abatement_age_comparator else None
        ),
        "abatement_age_unit": cond.abatement_age_unit,
        "abatement_age_system": cond.abatement_age_system,
        "abatement_age_code": cond.abatement_age_code,
        "abatement_period_start": (
            cond.abatement_period_start.isoformat() if cond.abatement_period_start else None
        ),
        "abatement_period_end": (
            cond.abatement_period_end.isoformat() if cond.abatement_period_end else None
        ),
        "abatement_range_low_value": (
            float(cond.abatement_range_low_value) if cond.abatement_range_low_value is not None else None
        ),
        "abatement_range_low_unit": cond.abatement_range_low_unit,
        "abatement_range_low_system": cond.abatement_range_low_system,
        "abatement_range_low_code": cond.abatement_range_low_code,
        "abatement_range_high_value": (
            float(cond.abatement_range_high_value) if cond.abatement_range_high_value is not None else None
        ),
        "abatement_range_high_unit": cond.abatement_range_high_unit,
        "abatement_range_high_system": cond.abatement_range_high_system,
        "abatement_range_high_code": cond.abatement_range_high_code,
        "abatement_string": cond.abatement_string,
        "recorded_date": (
            cond.recorded_date.isoformat() if cond.recorded_date else None
        ),
        "recorder": _plain_reference(cond, "recorder"),
        "asserter": _plain_reference(cond, "asserter"),
        "stages": [plain_condition_stage(s) for s in (cond.stages or [])],
        "evidence": [plain_condition_evidence(e) for e in (cond.evidence or [])],
        "notes": [plain_condition_note(n) for n in (cond.notes or [])],
        "identifiers": [
            plain_condition_identifier(i) for i in (cond.identifiers or [])
        ],
        "extension": cond.extension or [],
        "org_id": cond.tenant_id,
        "created_at": cond.created_at.isoformat() if cond.created_at else None,
        "updated_at": cond.updated_at.isoformat() if cond.updated_at else None,
        "created_by": cond.created_by,
        "updated_by": cond.updated_by,
    }
