"""Payload -> FHIR JSON conversion for EpisodeOfCare.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(EpisodeOfCareCreateSchema / EpisodeOfCarePatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.schemas.episode_of_care.input import (
        EpisodeOfCareCodeableConceptInput,
        EpisodeOfCareCreateSchema,
        EpisodeOfCareDiagnosisInput,
        EpisodeOfCareIdentifierInput,
        EpisodeOfCarePatchSchema,
        EpisodeOfCareStatusHistoryInput,
    )


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
    if d.condition:
        cond: dict[str, Any] = {"reference": d.condition}
        if d.condition_display:
            cond["display"] = d.condition_display
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

    if i.assigner:
        assigner: dict[str, Any] = {"reference": i.assigner}
        if i.assigner_display:
            assigner["display"] = i.assigner_display
        ident["assigner"] = assigner

    return ident


def payload_to_fhir_episode_of_care(payload: EpisodeOfCareCreateSchema) -> dict[str, Any]:
    """Convert an EpisodeOfCareCreateSchema to a FHIR R4 dict for pre-write validation."""
    fhir: dict[str, Any] = {
        "resourceType": "EpisodeOfCare",
        "status": fhir_enum(payload.status),
    }

    if payload.patient:
        pat: dict[str, Any] = {"reference": payload.patient}
        if payload.patient_display:
            pat["display"] = payload.patient_display
        fhir["patient"] = pat

    if payload.managing_organization:
        org: dict[str, Any] = {"reference": payload.managing_organization}
        if payload.managing_organization_display:
            org["display"] = payload.managing_organization_display
        fhir["managingOrganization"] = org

    p: dict[str, Any] = {}
    if payload.period_start:
        p["start"] = payload.period_start.isoformat()
    if payload.period_end:
        p["end"] = payload.period_end.isoformat()
    if p:
        fhir["period"] = p

    if payload.care_manager:
        cm: dict[str, Any] = {"reference": payload.care_manager}
        if payload.care_manager_display:
            cm["display"] = payload.care_manager_display
        fhir["careManager"] = cm

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
        fhir["referralRequest"] = [{"reference": r} for r in payload.referral_request if r]

    if payload.team:
        fhir["team"] = [{"reference": t} for t in payload.team if t]

    if payload.account:
        fhir["account"] = [{"reference": a} for a in payload.account if a]

    if payload.identifier:
        identifiers = [_identifier_from_payload(i) for i in payload.identifier]
        identifiers = [i for i in identifiers if i]
        if identifiers:
            fhir["identifier"] = identifiers

    return fhir


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

    if "patient" in fields_set or "patient_display" in fields_set:
        touched.add("patient")
        if payload.patient is not None:
            pat: dict[str, Any] = {"reference": payload.patient}
            if payload.patient_display:
                pat["display"] = payload.patient_display
            fragment["patient"] = pat

    if "managing_organization" in fields_set or "managing_organization_display" in fields_set:
        touched.add("managingOrganization")
        if payload.managing_organization is not None:
            org: dict[str, Any] = {"reference": payload.managing_organization}
            if payload.managing_organization_display:
                org["display"] = payload.managing_organization_display
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

    if "care_manager" in fields_set or "care_manager_display" in fields_set:
        touched.add("careManager")
        if payload.care_manager is not None:
            cm: dict[str, Any] = {"reference": payload.care_manager}
            if payload.care_manager_display:
                cm["display"] = payload.care_manager_display
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
            fragment["referralRequest"] = [{"reference": r} for r in payload.referral_request if r]

    if "team" in fields_set:
        touched.add("team")
        if payload.team is not None:
            fragment["team"] = [{"reference": t} for t in payload.team if t]

    if "account" in fields_set:
        touched.add("account")
        if payload.account is not None:
            fragment["account"] = [{"reference": a} for a in payload.account if a]

    if "identifier" in fields_set:
        touched.add("identifier")
        if payload.identifier is not None:
            fragment["identifier"] = [_identifier_from_payload(i) for i in payload.identifier]

    return fragment, touched
