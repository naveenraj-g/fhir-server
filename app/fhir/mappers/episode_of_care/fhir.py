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


def _fhir_reference(obj, prefix: str) -> dict | None:
    if obj is None:
        return None
    raw_reference = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    ref_str = raw_reference or (
        f"{fhir_enum(ref_type)}/{ref_id}" if ref_type and ref_id else None
    )

    entry: dict = {}
    if ref_str:
        entry["reference"] = ref_str
    if display:
        entry["display"] = display

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    id_type_system = getattr(obj, f"{prefix}_identifier_type_system", None)
    id_type_version = getattr(obj, f"{prefix}_identifier_type_version", None)
    id_type_code = getattr(obj, f"{prefix}_identifier_type_code", None)
    id_type_display = getattr(obj, f"{prefix}_identifier_type_display", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)
    id_type_user_selected = getattr(obj, f"{prefix}_identifier_type_user_selected", None)
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
        or id_type_text
        or (id_type_user_selected is not None)
        or id_system
        or id_value
        or id_period_start
        or id_period_end
    ):
        ident: dict = {}
        if id_use:
            ident["use"] = fhir_enum(id_use)
        if (
            id_type_system
            or id_type_version
            or id_type_code
            or id_type_display
            or id_type_text
            or (id_type_user_selected is not None)
        ):
            type_dict: dict = {}
            if (
                id_type_system
                or id_type_version
                or id_type_code
                or id_type_display
                or (id_type_user_selected is not None)
            ):
                coding_dict: dict = {}
                if id_type_system:
                    coding_dict["system"] = id_type_system
                if id_type_version:
                    coding_dict["version"] = id_type_version
                if id_type_code:
                    coding_dict["code"] = id_type_code
                if id_type_display:
                    coding_dict["display"] = id_type_display
                if id_type_user_selected is not None:
                    coding_dict["userSelected"] = id_type_user_selected
                type_dict["coding"] = [coding_dict]
            if id_type_text:
                type_dict["text"] = id_type_text
            ident["type"] = type_dict
        if id_system:
            ident["system"] = id_system
        if id_value:
            ident["value"] = id_value
        if id_period_start or id_period_end:
            p_dict: dict = {}
            if id_period_start:
                p_dict["start"] = fhir_instant(id_period_start)
            if id_period_end:
                p_dict["end"] = fhir_instant(id_period_end)
            ident["period"] = p_dict
        entry["identifier"] = ident

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
        assigner = _fhir_reference(ident, "assigner")
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
        cond = _fhir_reference(d, "condition")
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

    patient_ref = _fhir_reference(model, "patient")
    if patient_ref:
        fhir["patient"] = patient_ref

    managing_org_ref = _fhir_reference(model, "managing_organization")
    if managing_org_ref:
        fhir["managingOrganization"] = managing_org_ref

    period = _fhir_period(model.period_start, model.period_end)
    if period:
        fhir["period"] = period

    if model.referral_requests:
        referrals = [
            _fhir_reference(r, "reference")
            for r in model.referral_requests
        ]
        referrals = [r for r in referrals if r]
        if referrals:
            fhir["referralRequest"] = referrals

    care_manager_ref = _fhir_reference(model, "care_manager")
    if care_manager_ref:
        fhir["careManager"] = care_manager_ref

    if model.teams:
        teams = [
            _fhir_reference(t, "reference")
            for t in model.teams
        ]
        teams = [t for t in teams if t]
        if teams:
            fhir["team"] = teams

    if model.accounts:
        accounts = [
            _fhir_reference(a, "reference")
            for a in model.accounts
        ]
        accounts = [a for a in accounts if a]
        if accounts:
            fhir["account"] = accounts

    if model.extension:
        fhir["extension"] = model.extension

    return {k: v for k, v in fhir.items() if v is not None}
