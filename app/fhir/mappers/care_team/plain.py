from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum
from app.repository._reference_shared import _IDENTIFIER_FALLBACK_SUFFIXES

if TYPE_CHECKING:
    from app.models.care_team import CareTeamModel


def _plain_reference_fields(obj, prefix: str) -> dict:
    d = {}
    for s in _IDENTIFIER_FALLBACK_SUFFIXES:
        val = getattr(obj, f"{prefix}_{s}", None)
        if val is not None:
            if hasattr(val, "isoformat"):
                d[f"{prefix}_{s}"] = val.isoformat()
            elif hasattr(val, "value"):
                d[f"{prefix}_{s}"] = val.value
            else:
                d[f"{prefix}_{s}"] = val
        else:
            d[f"{prefix}_{s}"] = None
    return d


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
        result.append(entry)
    return result


def _plain_identifier(i) -> dict:
    d = {
        "id": i.id,
        "use": fhir_enum(i.use) if i.use else None,
        "type_text": i.type_text,
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start.isoformat() if i.period_start else None,
        "period_end": i.period_end.isoformat() if i.period_end else None,
        "assigner": i.assigner_reference,
        "assigner_type": fhir_enum(i.assigner_type) if i.assigner_type else None,
        "assigner_id": i.assigner_id,
        "assigner_display": i.assigner_display,
        "type_codings": _plain_coding_list(getattr(i, "type_codings", None)),
    }
    d.update(_plain_reference_fields(i, "assigner"))
    return d


def _plain_category(c) -> dict:
    return {
        "id": c.id,
        "text": c.text,
        "codings": _plain_coding_list(getattr(c, "codings", None)),
    }


def _plain_participant_role(r) -> dict:
    return {
        "id": r.id,
        "text": r.text,
        "codings": _plain_coding_list(getattr(r, "codings", None)),
    }


def _plain_participant(p) -> dict:
    d = {
        "id": p.id,
        "roles": [_plain_participant_role(r) for r in getattr(p, "roles", []) or []],
        "member": p.member_reference,
        "member_type": fhir_enum(p.member_type) if p.member_type else None,
        "member_id": p.member_id,
        "member_display": p.member_display,
        "on_behalf_of": p.on_behalf_of_reference,
        "on_behalf_of_type": fhir_enum(p.on_behalf_of_type) if p.on_behalf_of_type else None,
        "on_behalf_of_id": p.on_behalf_of_id,
        "on_behalf_of_display": p.on_behalf_of_display,
        "period_start": p.period_start.isoformat() if p.period_start else None,
        "period_end": p.period_end.isoformat() if p.period_end else None,
    }
    d.update(_plain_reference_fields(p, "member"))
    d.update(_plain_reference_fields(p, "on_behalf_of"))
    return d


def _plain_reason_code(r) -> dict:
    return {
        "id": r.id,
        "text": r.text,
        "codings": _plain_coding_list(getattr(r, "codings", None)),
    }


def _plain_ref_row(r) -> dict:
    d = {
        "id": r.id,
        "reference": r.reference_reference,
        "type": fhir_enum(r.reference_type) if r.reference_type else None,
        "reference_id": r.reference_id,
        "display": r.reference_display,
    }
    for s in _IDENTIFIER_FALLBACK_SUFFIXES:
        val = getattr(r, f"reference_{s}", None)
        if val is not None:
            if hasattr(val, "isoformat"):
                d[s] = val.isoformat()
            elif hasattr(val, "value"):
                d[s] = val.value
            else:
                d[s] = val
        else:
            d[s] = None
    return d


def _plain_telecom(t) -> dict:
    return {
        "id": t.id,
        "system": fhir_enum(t.system) if t.system else None,
        "value": t.value,
        "use": fhir_enum(t.use) if t.use else None,
        "rank": t.rank,
        "period_start": t.period_start.isoformat() if t.period_start else None,
        "period_end": t.period_end.isoformat() if t.period_end else None,
    }


def _plain_note(n) -> dict:
    return {
        "id": n.id,
        "text": n.text,
        "time": n.time.isoformat() if n.time else None,
        "author_string": n.author_string,
        "author_reference": n.author_reference_reference,
        "author_reference_type": fhir_enum(n.author_reference_type) if n.author_reference_type else None,
        "author_reference_id": n.author_reference_id,
        "author_reference_display": n.author_reference_display,
    }


def to_plain_care_team(model: CareTeamModel) -> dict:
    """Convert CareTeamModel to snake_case plain dictionary."""
    d = {
        "id": model.care_team_id,
        "status": fhir_enum(model.status) if model.status else None,
        "name": model.name,
        "subject": model.subject_reference,
        "subject_id": model.subject_id,
        "subject_type": fhir_enum(model.subject_type) if model.subject_type else None,
        "subject_display": model.subject_display,
        "encounter": model.encounter_reference,
        "encounter_id": model.encounter_id,
        "encounter_type": fhir_enum(model.encounter_type) if model.encounter_type else None,
        "encounter_display": model.encounter_display,
        "period_start": model.period_start.isoformat() if model.period_start else None,
        "period_end": model.period_end.isoformat() if model.period_end else None,
        "identifiers": [_plain_identifier(i) for i in model.identifiers or []],
        "categories": [_plain_category(c) for c in model.categories or []],
        "participants": [_plain_participant(p) for p in model.participants or []],
        "reason_codes": [_plain_reason_code(r) for r in model.reason_codes or []],
        "reason_references": [_plain_ref_row(r) for r in model.reason_references or []],
        "managing_organizations": [_plain_ref_row(m) for m in model.managing_organizations or []],
        "telecoms": [_plain_telecom(t) for t in model.telecoms or []],
        "notes": [_plain_note(n) for n in model.notes or []],
        "tenant_id": model.tenant_id,
        "created_by": model.created_by,
        "updated_by": model.updated_by,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }
    d.update(_plain_reference_fields(model, "subject"))
    d.update(_plain_reference_fields(model, "encounter"))
    return d
