from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.models.episode_of_care import EpisodeOfCareModel


def _plain_codings(codings) -> list[dict]:
    result = []
    for c in codings or []:
        result.append({
            "id": c.id,
            "system": c.system,
            "version": c.version,
            "code": c.code,
            "display": c.display,
            "user_selected": c.user_selected,
            "tenant_id": c.tenant_id,
            "created_by": c.created_by,
            "updated_by": c.updated_by,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        })
    return result


def _plain_ref(ref_raw: str | None, ref_type, ref_id: int | None) -> str | None:
    if ref_raw:
        return ref_raw
    if ref_type and ref_id:
        return f"{fhir_enum(ref_type)}/{ref_id}"
    return None


def to_plain_episode_of_care(model: EpisodeOfCareModel) -> dict[str, Any]:
    """Convert an EpisodeOfCareModel to a plain snake_case dict."""
    return {
        "id": model.episode_of_care_id,
        "status": fhir_enum(model.status) if model.status else None,
        "patient": _plain_ref(model.patient_reference, model.patient_type, model.patient_id),
        "patient_display": model.patient_display,
        "managing_organization": _plain_ref(
            model.managing_organization_reference,
            model.managing_organization_type,
            model.managing_organization_id,
        ),
        "managing_organization_display": model.managing_organization_display,
        "period_start": model.period_start,
        "period_end": model.period_end,
        "care_manager": _plain_ref(
            model.care_manager_reference,
            model.care_manager_type,
            model.care_manager_id,
        ),
        "care_manager_display": model.care_manager_display,
        "tenant_id": model.tenant_id,
        "created_by": model.created_by,
        "updated_by": model.updated_by,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
        "identifiers": [
            {
                "id": ident.id,
                "use": fhir_enum(ident.use) if ident.use else None,
                "type_text": ident.type_text,
                "system": ident.system,
                "value": ident.value,
                "period_start": ident.period_start,
                "period_end": ident.period_end,
                "assigner_reference": ident.assigner_reference,
                "assigner_type": fhir_enum(ident.assigner_type) if ident.assigner_type else None,
                "assigner_id": ident.assigner_id,
                "assigner_display": ident.assigner_display,
                "type_codings": _plain_codings(ident.type_codings),
                "tenant_id": ident.tenant_id,
                "created_by": ident.created_by,
                "updated_by": ident.updated_by,
                "created_at": ident.created_at,
                "updated_at": ident.updated_at,
            }
            for ident in (model.identifiers or [])
        ],
        "status_history": [
            {
                "id": sh.id,
                "status": fhir_enum(sh.status) if sh.status else None,
                "period_start": sh.period_start,
                "period_end": sh.period_end,
                "tenant_id": sh.tenant_id,
                "created_by": sh.created_by,
                "updated_by": sh.updated_by,
                "created_at": sh.created_at,
                "updated_at": sh.updated_at,
            }
            for sh in (model.status_history or [])
        ],
        "types": [
            {
                "id": t.id,
                "text": t.text,
                "codings": _plain_codings(t.codings),
                "tenant_id": t.tenant_id,
                "created_by": t.created_by,
                "updated_by": t.updated_by,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
            }
            for t in (model.types or [])
        ],
        "diagnoses": [
            {
                "id": d.id,
                "condition": _plain_ref(d.condition_reference, d.condition_type, d.condition_id),
                "condition_display": d.condition_display,
                "role_text": d.role_text,
                "role_codings": _plain_codings(d.role_codings),
                "rank": d.rank,
                "tenant_id": d.tenant_id,
                "created_by": d.created_by,
                "updated_by": d.updated_by,
                "created_at": d.created_at,
                "updated_at": d.updated_at,
            }
            for d in (model.diagnoses or [])
        ],
        "referral_requests": [
            {
                "id": r.id,
                "reference": _plain_ref(r.reference_reference, r.reference_type, r.reference_id),
                "display": r.reference_display,
                "tenant_id": r.tenant_id,
                "created_by": r.created_by,
                "updated_by": r.updated_by,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }
            for r in (model.referral_requests or [])
        ],
        "teams": [
            {
                "id": t.id,
                "reference": _plain_ref(t.reference_reference, t.reference_type, t.reference_id),
                "display": t.reference_display,
                "tenant_id": t.tenant_id,
                "created_by": t.created_by,
                "updated_by": t.updated_by,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
            }
            for t in (model.teams or [])
        ],
        "accounts": [
            {
                "id": a.id,
                "reference": _plain_ref(a.reference_reference, a.reference_type, a.reference_id),
                "display": a.reference_display,
                "tenant_id": a.tenant_id,
                "created_by": a.created_by,
                "updated_by": a.updated_by,
                "created_at": a.created_at,
                "updated_at": a.updated_at,
            }
            for a in (model.accounts or [])
        ],
    }
