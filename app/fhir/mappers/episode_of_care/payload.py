"""Payload -> FHIR JSON conversion for EpisodeOfCare.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(EpisodeOfCareCreateSchema / EpisodeOfCarePatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum
from app.repository._reference_shared import _IDENTIFIER_FALLBACK_SUFFIXES

if TYPE_CHECKING:
    from app.schemas.episode_of_care.input import (
        EpisodeOfCareCodeableConceptInput,
        EpisodeOfCareCreateSchema,
        EpisodeOfCareDiagnosisInput,
        EpisodeOfCareIdentifierInput,
        EpisodeOfCarePatchSchema,
        EpisodeOfCareStatusHistoryInput,
    )


def _reference_from_payload(obj: Any, prefix: str) -> dict | None:
    if not obj:
        return None

    def _get(field):
        return obj.get(field) if isinstance(obj, dict) else getattr(obj, field, None)

    raw_reference = _get(prefix)
    if raw_reference is None and prefix != "reference":
        raw_reference = _get(f"{prefix}_reference")
    display = _get(f"{prefix}_display")
    if display is None and prefix == "reference":
        display = _get("display")

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    if display:
        entry["display"] = display

    id_use = _get(f"{prefix}_identifier_use") or _get("identifier_use")
    id_type_system = _get(f"{prefix}_identifier_type_system") or _get("identifier_type_system")
    id_type_version = _get(f"{prefix}_identifier_type_version") or _get("identifier_type_version")
    id_type_code = _get(f"{prefix}_identifier_type_code") or _get("identifier_type_code")
    id_type_display = _get(f"{prefix}_identifier_type_display") or _get("identifier_type_display")
    id_type_text = _get(f"{prefix}_identifier_type_text") or _get("identifier_type_text")
    id_type_user_selected = (
        _get(f"{prefix}_identifier_type_user_selected")
        if _get(f"{prefix}_identifier_type_user_selected") is not None
        else _get("identifier_type_user_selected")
    )
    id_system = _get(f"{prefix}_identifier_system") or _get("identifier_system")
    id_value = _get(f"{prefix}_identifier_value") or _get("identifier_value")
    id_period_start = _get(f"{prefix}_identifier_period_start") or _get("identifier_period_start")
    id_period_end = _get(f"{prefix}_identifier_period_end") or _get("identifier_period_end")

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
                p_dict["start"] = (
                    id_period_start.isoformat()
                    if hasattr(id_period_start, "isoformat")
                    else str(id_period_start)
                )
            if id_period_end:
                p_dict["end"] = (
                    id_period_end.isoformat()
                    if hasattr(id_period_end, "isoformat")
                    else str(id_period_end)
                )
            ident["period"] = p_dict
        entry["identifier"] = ident

    return entry or None


def _child_reference_from_payload(item: Any) -> dict | None:
    if isinstance(item, str):
        return {"reference": item}
    return _reference_from_payload(item, "reference")


def _coding_from_payload(c) -> dict:
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
    concept: EpisodeOfCareCodeableConceptInput | None,
) -> dict | None:
    if not concept:
        return None
    codings = [_coding_from_payload(c) for c in (concept.coding or [])]
    codings = [c for c in codings if c]
    result: dict = {}
    if codings:
        result["coding"] = codings
    if concept.text:
        result["text"] = concept.text
    return result or None


def _status_history_from_payload(h: EpisodeOfCareStatusHistoryInput) -> dict:
    entry: dict[str, Any] = {"status": fhir_enum(h.status)}
    p: dict[str, Any] = {}
    if h.period_start:
        p["start"] = h.period_start.isoformat()
    if h.period_end:
        p["end"] = h.period_end.isoformat()
    if p:
        entry["period"] = p
    return entry


def _diagnosis_from_payload(d: EpisodeOfCareDiagnosisInput) -> dict:
    diag: dict[str, Any] = {}
    cond = _reference_from_payload(d, "condition")
    if cond:
        diag["condition"] = cond
    if d.role:
        role = _codeable_concept_from_payload(d.role)
        if role:
            diag["role"] = role
    if d.rank is not None:
        diag["rank"] = d.rank
    return diag


def _identifier_from_payload(i: EpisodeOfCareIdentifierInput) -> dict:
    ident: dict[str, Any] = {}
    if i.use:
        ident["use"] = fhir_enum(i.use)
    if i.system:
        ident["system"] = i.system
    if i.value:
        ident["value"] = i.value

    codings = [_coding_from_payload(c) for c in (i.type_codings or [])]
    codings = [c for c in codings if c]
    type_dict: dict[str, Any] = {}
    if codings:
        type_dict["coding"] = codings
    if i.type_text:
        type_dict["text"] = i.type_text
    if type_dict:
        ident["type"] = type_dict

    period: dict[str, Any] = {}
    if i.period_start:
        period["start"] = i.period_start.isoformat()
    if i.period_end:
        period["end"] = i.period_end.isoformat()
    if period:
        ident["period"] = period

    assigner = _reference_from_payload(i, "assigner")
    if assigner:
        ident["assigner"] = assigner

    return ident


def payload_to_fhir_episode_of_care(payload: EpisodeOfCareCreateSchema) -> dict[str, Any]:
    """Convert an EpisodeOfCareCreateSchema to a FHIR R4 dict for pre-write validation."""
    fhir: dict[str, Any] = {
        "resourceType": "EpisodeOfCare",
        "status": fhir_enum(payload.status),
    }

    patient = _reference_from_payload(payload, "patient")
    if patient:
        fhir["patient"] = patient

    managing_org = _reference_from_payload(payload, "managing_organization")
    if managing_org:
        fhir["managingOrganization"] = managing_org

    p: dict[str, Any] = {}
    if payload.period_start:
        p["start"] = payload.period_start.isoformat()
    if payload.period_end:
        p["end"] = payload.period_end.isoformat()
    if p:
        fhir["period"] = p

    care_manager = _reference_from_payload(payload, "care_manager")
    if care_manager:
        fhir["careManager"] = care_manager

    if payload.status_history:
        history = [_status_history_from_payload(h) for h in payload.status_history]
        if history:
            fhir["statusHistory"] = history

    if payload.type:
        types = [_codeable_concept_from_payload(t) for t in payload.type]
        types = [t for t in types if t]
        if types:
            fhir["type"] = types

    if payload.diagnosis:
        diagnoses = [_diagnosis_from_payload(d) for d in payload.diagnosis]
        diagnoses = [d for d in diagnoses if d]
        if diagnoses:
            fhir["diagnosis"] = diagnoses

    if payload.referral_request:
        rr = [_child_reference_from_payload(r) for r in payload.referral_request]
        rr = [r for r in rr if r]
        if rr:
            fhir["referralRequest"] = rr

    if payload.team:
        teams = [_child_reference_from_payload(t) for t in payload.team]
        teams = [t for t in teams if t]
        if teams:
            fhir["team"] = teams

    if payload.account:
        accounts = [_child_reference_from_payload(a) for a in payload.account]
        accounts = [a for a in accounts if a]
        if accounts:
            fhir["account"] = accounts

    if payload.identifier:
        identifiers = [_identifier_from_payload(i) for i in payload.identifier]
        identifiers = [i for i in identifiers if i]
        if identifiers:
            fhir["identifier"] = identifiers

    return fhir


_PATIENT_FIELDS = {"patient", "patient_display"} | {f"patient_{s}" for s in _IDENTIFIER_FALLBACK_SUFFIXES}
_MANAGING_ORG_FIELDS = {"managing_organization", "managing_organization_display"} | {f"managing_organization_{s}" for s in _IDENTIFIER_FALLBACK_SUFFIXES}
_CARE_MANAGER_FIELDS = {"care_manager", "care_manager_display"} | {f"care_manager_{s}" for s in _IDENTIFIER_FALLBACK_SUFFIXES}


def patch_fragment_to_fhir_episode_of_care(
    payload: EpisodeOfCarePatchSchema,
) -> tuple[dict, set[str]]:
    """Map touched fields of EpisodeOfCarePatchSchema to a partial FHIR dict and set of touched keys."""
    touched: set[str] = set()
    fragment: dict = {}
    fields_set = payload.model_fields_set

    if "status" in fields_set:
        touched.add("status")
        if payload.status is not None:
            fragment["status"] = fhir_enum(payload.status)

    if fields_set & _PATIENT_FIELDS:
        touched.add("patient")
        pat = _reference_from_payload(payload, "patient")
        if pat:
            fragment["patient"] = pat

    if fields_set & _MANAGING_ORG_FIELDS:
        touched.add("managingOrganization")
        org = _reference_from_payload(payload, "managing_organization")
        if org:
            fragment["managingOrganization"] = org

    if "period_start" in fields_set or "period_end" in fields_set:
        touched.add("period")
        p: dict[str, Any] = {}
        if payload.period_start:
            p["start"] = payload.period_start.isoformat()
        if payload.period_end:
            p["end"] = payload.period_end.isoformat()
        if p:
            fragment["period"] = p

    if fields_set & _CARE_MANAGER_FIELDS:
        touched.add("careManager")
        cm = _reference_from_payload(payload, "care_manager")
        if cm:
            fragment["careManager"] = cm

    if "status_history" in fields_set:
        touched.add("statusHistory")
        if payload.status_history is not None:
            fragment["statusHistory"] = [
                _status_history_from_payload(h) for h in payload.status_history
            ]

    if "type" in fields_set:
        touched.add("type")
        if payload.type is not None:
            fragment["type"] = [
                t for t in [_codeable_concept_from_payload(x) for x in payload.type] if t
            ]

    if "diagnosis" in fields_set:
        touched.add("diagnosis")
        if payload.diagnosis is not None:
            fragment["diagnosis"] = [
                d for d in [_diagnosis_from_payload(x) for x in payload.diagnosis] if d
            ]

    if "referral_request" in fields_set:
        touched.add("referralRequest")
        if payload.referral_request is not None:
            fragment["referralRequest"] = [
                _child_reference_from_payload(r)
                for r in payload.referral_request
                if _child_reference_from_payload(r)
            ]

    if "team" in fields_set:
        touched.add("team")
        if payload.team is not None:
            fragment["team"] = [
                _child_reference_from_payload(t)
                for t in payload.team
                if _child_reference_from_payload(t)
            ]

    if "account" in fields_set:
        touched.add("account")
        if payload.account is not None:
            fragment["account"] = [
                _child_reference_from_payload(a)
                for a in payload.account
                if _child_reference_from_payload(a)
            ]

    if "identifier" in fields_set:
        touched.add("identifier")
        if payload.identifier is not None:
            fragment["identifier"] = [_identifier_from_payload(i) for i in payload.identifier]

    return fragment, touched
