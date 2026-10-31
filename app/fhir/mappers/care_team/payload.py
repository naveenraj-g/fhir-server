"""Payload -> FHIR JSON conversion for CareTeam.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(CareTeamCreateSchema / CareTeamPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.schemas.care_team.input import (
        CareTeamCodeableConceptInput,
        CareTeamCreateSchema,
        CareTeamIdentifierInput,
        CareTeamNoteInput,
        CareTeamParticipantInput,
        CareTeamPatchSchema,
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


def _codeable_concept_from_payload(concept: CareTeamCodeableConceptInput | None) -> dict | None:
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


def _participant_from_payload(p: CareTeamParticipantInput) -> dict:
    result: dict[str, Any] = {}
    if p.role:
        roles_fhir = [_codeable_concept_from_payload(r) for r in p.role]
        roles_fhir = [r for r in roles_fhir if r]
        if roles_fhir:
            result["role"] = roles_fhir
    if p.member:
        member: dict[str, Any] = {"reference": p.member}
        if p.member_display:
            member["display"] = p.member_display
        result["member"] = member
    if p.on_behalf_of:
        on_behalf: dict[str, Any] = {"reference": p.on_behalf_of}
        if p.on_behalf_of_display:
            on_behalf["display"] = p.on_behalf_of_display
        result["onBehalfOf"] = on_behalf
    period: dict[str, Any] = {}
    if p.period_start:
        period["start"] = p.period_start.isoformat()
    if p.period_end:
        period["end"] = p.period_end.isoformat()
    if period:
        result["period"] = period
    return result


def _telecom_from_payload(t) -> dict:
    if isinstance(t, dict):
        result: dict[str, Any] = {}
        if t.get("system"):
            result["system"] = fhir_enum(t["system"])
        if t.get("value"):
            result["value"] = t["value"]
        if t.get("use"):
            result["use"] = fhir_enum(t["use"])
        if t.get("rank") is not None:
            result["rank"] = t["rank"]
        return result

    result = {}
    if t.system:
        result["system"] = fhir_enum(t.system)
    if t.value:
        result["value"] = t.value
    if t.use:
        result["use"] = fhir_enum(t.use)
    if t.rank is not None:
        result["rank"] = t.rank
    if getattr(t, "period_start", None) or getattr(t, "period_end", None):
        period: dict[str, Any] = {}
        if getattr(t, "period_start", None):
            period["start"] = t.period_start.isoformat()
        if getattr(t, "period_end", None):
            period["end"] = t.period_end.isoformat()
        result["period"] = period
    return result


def _note_from_payload(n: CareTeamNoteInput) -> dict:
    result: dict[str, Any] = {"text": n.text}
    if n.time:
        result["time"] = n.time.isoformat()
    if n.author_string:
        result["authorString"] = n.author_string
    if n.author_reference:
        auth_ref: dict[str, Any] = {"reference": n.author_reference}
        if n.author_reference_display:
            auth_ref["display"] = n.author_reference_display
        result["authorReference"] = auth_ref
    return result


def _identifier_from_payload(i: CareTeamIdentifierInput) -> dict:
    result: dict[str, Any] = {}
    if i.use:
        result["use"] = fhir_enum(i.use)
    if i.type:
        type_cc = _codeable_concept_from_payload(i.type)
        if type_cc:
            result["type"] = type_cc
    if i.system:
        result["system"] = i.system
    if i.value:
        result["value"] = i.value
    if i.period_start or i.period_end:
        p: dict[str, Any] = {}
        if i.period_start:
            p["start"] = i.period_start.isoformat()
        if i.period_end:
            p["end"] = i.period_end.isoformat()
        result["period"] = p
    if i.assigner:
        assigner: dict[str, Any] = {"reference": i.assigner}
        if i.assigner_display:
            assigner["display"] = i.assigner_display
        result["assigner"] = assigner
    return result


def payload_to_fhir_care_team(payload: CareTeamCreateSchema) -> dict:
    """Map a CareTeamCreateSchema to full FHIR R4 JSON for pre-insert validation."""
    fhir: dict[str, Any] = {
        "resourceType": "CareTeam",
    }

    if payload.status is not None:
        fhir["status"] = fhir_enum(payload.status)

    if payload.name is not None:
        fhir["name"] = payload.name

    if payload.subject is not None:
        subj: dict[str, Any] = {"reference": payload.subject}
        if payload.subject_display:
            subj["display"] = payload.subject_display
        fhir["subject"] = subj

    if payload.encounter is not None:
        enc: dict[str, Any] = {"reference": payload.encounter}
        if payload.encounter_display:
            enc["display"] = payload.encounter_display
        fhir["encounter"] = enc

    if payload.period_start is not None or payload.period_end is not None:
        p: dict[str, Any] = {}
        if payload.period_start:
            p["start"] = payload.period_start.isoformat()
        if payload.period_end:
            p["end"] = payload.period_end.isoformat()
        fhir["period"] = p

    if payload.category:
        cats = [_codeable_concept_from_payload(c) for c in payload.category]
        cats = [c for c in cats if c]
        if cats:
            fhir["category"] = cats

    if payload.participant:
        participants = [_participant_from_payload(p) for p in payload.participant]
        participants = [p for p in participants if p]
        if participants:
            fhir["participant"] = participants

    if payload.reason_code:
        reasons = [_codeable_concept_from_payload(r) for r in payload.reason_code]
        reasons = [r for r in reasons if r]
        if reasons:
            fhir["reasonCode"] = reasons

    if payload.reason_reference:
        fhir["reasonReference"] = [{"reference": r} for r in payload.reason_reference if r]

    if payload.managing_organization:
        fhir["managingOrganization"] = [{"reference": m} for m in payload.managing_organization if m]

    if payload.telecom:
        telecoms = [_telecom_from_payload(t) for t in payload.telecom]
        telecoms = [t for t in telecoms if t]
        if telecoms:
            fhir["telecom"] = telecoms

    if payload.note:
        notes = [_note_from_payload(n) for n in payload.note]
        notes = [n for n in notes if n]
        if notes:
            fhir["note"] = notes

    if payload.identifier:
        identifiers = [_identifier_from_payload(i) for i in payload.identifier]
        identifiers = [i for i in identifiers if i]
        if identifiers:
            fhir["identifier"] = identifiers

    return fhir


def patch_fragment_to_fhir_care_team(
    payload: CareTeamPatchSchema,
) -> tuple[dict, set[str]]:
    """Map touched fields of CareTeamPatchSchema to a partial FHIR dict and set of touched keys."""
    touched: set[str] = set()
    fragment: dict = {}
    fields_set = payload.model_fields_set

    if "status" in fields_set:
        touched.add("status")
        if payload.status is not None:
            fragment["status"] = fhir_enum(payload.status)

    if "name" in fields_set:
        touched.add("name")
        if payload.name is not None:
            fragment["name"] = payload.name

    if "subject" in fields_set or "subject_display" in fields_set:
        touched.add("subject")
        if payload.subject is not None:
            subj: dict[str, Any] = {"reference": payload.subject}
            if payload.subject_display:
                subj["display"] = payload.subject_display
            fragment["subject"] = subj

    if "encounter" in fields_set or "encounter_display" in fields_set:
        touched.add("encounter")
        if payload.encounter is not None:
            enc: dict[str, Any] = {"reference": payload.encounter}
            if payload.encounter_display:
                enc["display"] = payload.encounter_display
            fragment["encounter"] = enc

    if "period_start" in fields_set or "period_end" in fields_set:
        touched.add("period")
        p: dict[str, Any] = {}
        if payload.period_start:
            p["start"] = payload.period_start.isoformat()
        if payload.period_end:
            p["end"] = payload.period_end.isoformat()
        if p:
            fragment["period"] = p

    if "category" in fields_set:
        touched.add("category")
        if payload.category is not None:
            fragment["category"] = [
                c for c in [_codeable_concept_from_payload(x) for x in payload.category] if c
            ]

    if "participant" in fields_set:
        touched.add("participant")
        if payload.participant is not None:
            fragment["participant"] = [
                _participant_from_payload(x) for x in payload.participant
            ]

    if "reason_code" in fields_set:
        touched.add("reasonCode")
        if payload.reason_code is not None:
            fragment["reasonCode"] = [
                r for r in [_codeable_concept_from_payload(x) for x in payload.reason_code] if r
            ]

    if "reason_reference" in fields_set:
        touched.add("reasonReference")
        if payload.reason_reference is not None:
            fragment["reasonReference"] = [{"reference": r} for r in payload.reason_reference if r]

    if "managing_organization" in fields_set:
        touched.add("managingOrganization")
        if payload.managing_organization is not None:
            fragment["managingOrganization"] = [{"reference": m} for m in payload.managing_organization if m]

    if "telecom" in fields_set:
        touched.add("telecom")
        if payload.telecom is not None:
            fragment["telecom"] = [_telecom_from_payload(t) for t in payload.telecom]

    if "note" in fields_set:
        touched.add("note")
        if payload.note is not None:
            fragment["note"] = [_note_from_payload(n) for n in payload.note]

    if "identifier" in fields_set:
        touched.add("identifier")
        if payload.identifier is not None:
            fragment["identifier"] = [_identifier_from_payload(i) for i in payload.identifier]

    return fragment, touched
