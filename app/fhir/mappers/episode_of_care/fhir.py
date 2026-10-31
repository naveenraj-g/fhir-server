from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.episode_of_care import (
        EpisodeOfCareDiagnosis,
        EpisodeOfCareModel,
        EpisodeOfCareStatusHistory,
    )


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


def _fhir_ref(ref_raw: str | None, ref_type, ref_id: int | None, display: str | None) -> dict | None:
    result: dict = {}
    if ref_raw:
        result["reference"] = ref_raw
    elif ref_type and ref_id:
        result["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        result["display"] = display
    return result or None


def _fhir_reference_with_identifier_fallback(obj, prefix: str) -> dict | None:
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

    # Logical identifier fallback
    ident_system = getattr(obj, f"{prefix}_identifier_system", None)
    ident_value = getattr(obj, f"{prefix}_identifier_value", None)
    ident_use = getattr(obj, f"{prefix}_identifier_use", None)
    ident_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)

    identifier: dict = {}
    if ident_use:
        identifier["use"] = fhir_enum(ident_use)
    if ident_system:
        identifier["system"] = ident_system
    if ident_value:
        identifier["value"] = ident_value
    if ident_type_text:
        identifier["type"] = {"text": ident_type_text}

    if identifier:
        entry["identifier"] = identifier

    return entry or None


def _fhir_period(start, end) -> dict | None:
    p: dict = {}
    if start:
        p["start"] = fhir_instant(start)
    if end:
        p["end"] = fhir_instant(end)
    return p or None


def _fhir_identifiers(identifiers) -> list[dict]:
    result = []
    for ident in identifiers or []:
        entry: dict[str, Any] = {}
        if ident.use:
            entry["use"] = fhir_enum(ident.use)
        type_concept = _fhir_codeable_concept(ident.type_codings, ident.type_text)
        if type_concept:
            entry["type"] = type_concept
        if ident.system:
            entry["system"] = ident.system
        if ident.value:
            entry["value"] = ident.value
        period = _fhir_period(ident.period_start, ident.period_end)
        if period:
            entry["period"] = period
        assigner = _fhir_reference_with_identifier_fallback(ident, "assigner")
        if assigner:
            entry["assigner"] = assigner
        if entry:
            result.append(entry)
    return result


def _fhir_meta(model: EpisodeOfCareModel) -> dict:
    meta: dict[str, Any] = {}
    if model.updated_at:
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    elif model.created_at:
        meta["lastUpdated"] = fhir_instant(model.created_at)

    exts = []
    if model.created_at:
        exts.append({
            "url": "http://hl7.org/fhir/StructureDefinition/resource-created-at",
            "valueDateTime": fhir_instant(model.created_at),
        })
    if model.created_by:
        exts.append({
            "url": "http://hl7.org/fhir/StructureDefinition/resource-created-by",
            "valueString": model.created_by,
        })
    if model.updated_by:
        exts.append({
            "url": "http://hl7.org/fhir/StructureDefinition/resource-updated-by",
            "valueString": model.updated_by,
        })
    if exts:
        meta["extension"] = exts
    return meta


def _fhir_status_history(history: list[EpisodeOfCareStatusHistory]) -> list[dict]:
    result = []
    for h in history or []:
        entry: dict[str, Any] = {"status": fhir_enum(h.status)}
        period = _fhir_period(h.period_start, h.period_end)
        if period:
            entry["period"] = period
        result.append(entry)
    return result


def _fhir_diagnoses(diagnoses: list[EpisodeOfCareDiagnosis]) -> list[dict]:
    result = []
    for d in diagnoses or []:
        entry: dict[str, Any] = {}
        cond = _fhir_ref(d.condition_reference, d.condition_type, d.condition_id, d.condition_display)
        if cond:
            entry["condition"] = cond
        role = _fhir_codeable_concept(d.role_codings, d.role_text)
        if role:
            entry["role"] = role
        if d.rank is not None:
            entry["rank"] = d.rank
        if entry:
            result.append(entry)
    return result


def to_fhir_episode_of_care(model: EpisodeOfCareModel) -> dict[str, Any]:
    """Convert an EpisodeOfCareModel to a FHIR R4 EpisodeOfCare resource dict."""
    fhir: dict[str, Any] = {
        "resourceType": "EpisodeOfCare",
        "id": str(model.episode_of_care_id),
    }

    meta = _fhir_meta(model)
    if meta:
        fhir["meta"] = meta

    if model.status:
        fhir["status"] = fhir_enum(model.status)

    identifiers = _fhir_identifiers(model.identifiers)
    if identifiers:
        fhir["identifier"] = identifiers

    if model.status_history:
        sh = _fhir_status_history(model.status_history)
        if sh:
            fhir["statusHistory"] = sh

    if model.types:
        types = [_fhir_codeable_concept(t.codings, t.text) for t in model.types]
        types = [t for t in types if t]
        if types:
            fhir["type"] = types

    if model.diagnoses:
        diags = _fhir_diagnoses(model.diagnoses)
        if diags:
            fhir["diagnosis"] = diags

    patient_ref = _fhir_ref(
        model.patient_reference, model.patient_type, model.patient_id, model.patient_display
    )
    if patient_ref:
        fhir["patient"] = patient_ref

    managing_org_ref = _fhir_ref(
        model.managing_organization_reference,
        model.managing_organization_type,
        model.managing_organization_id,
        model.managing_organization_display,
    )
    if managing_org_ref:
        fhir["managingOrganization"] = managing_org_ref

    period = _fhir_period(model.period_start, model.period_end)
    if period:
        fhir["period"] = period

    if model.referral_requests:
        referrals = [
            _fhir_ref(r.reference_reference, r.reference_type, r.reference_id, r.reference_display)
            for r in model.referral_requests
        ]
        referrals = [r for r in referrals if r]
        if referrals:
            fhir["referralRequest"] = referrals

    care_manager_ref = _fhir_ref(
        model.care_manager_reference,
        model.care_manager_type,
        model.care_manager_id,
        model.care_manager_display,
    )
    if care_manager_ref:
        fhir["careManager"] = care_manager_ref

    if model.teams:
        teams = [
            _fhir_ref(t.reference_reference, t.reference_type, t.reference_id, t.reference_display)
            for t in model.teams
        ]
        teams = [t for t in teams if t]
        if teams:
            fhir["team"] = teams

    if model.accounts:
        accounts = [
            _fhir_ref(a.reference_reference, a.reference_type, a.reference_id, a.reference_display)
            for a in model.accounts
        ]
        accounts = [a for a in accounts if a]
        if accounts:
            fhir["account"] = accounts

    if model.extension:
        fhir["extension"] = model.extension

    return {k: v for k, v in fhir.items() if v is not None}
