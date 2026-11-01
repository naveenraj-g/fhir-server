"""Payload -> FHIR JSON conversion for CareTeam.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(CareTeamCreateSchema / CareTeamPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum
from app.repository._reference_shared import _IDENTIFIER_FALLBACK_SUFFIXES

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


def _child_reference_from_payload(r: Any) -> dict | None:
    if not r:
        return None
    if isinstance(r, str):
        return {"reference": r}
    return _reference_from_payload(r, "reference")


def _participant_from_payload(p: CareTeamParticipantInput) -> dict:
    result: dict[str, Any] = {}
    if p.role:
        roles_fhir = [_codeable_concept_from_payload(r) for r in p.role]
        roles_fhir = [r for r in roles_fhir if r]
        if roles_fhir:
            result["role"] = roles_fhir
    member = _reference_from_payload(p, "member")
    if member:
        result["member"] = member
    on_behalf = _reference_from_payload(p, "on_behalf_of")
    if on_behalf:
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
    assigner = _reference_from_payload(i, "assigner")
    if assigner:
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

    subj = _reference_from_payload(payload, "subject")
    if subj:
        fhir["subject"] = subj

    enc = _reference_from_payload(payload, "encounter")
    if enc:
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
        rr = [_child_reference_from_payload(r) for r in payload.reason_reference]
        rr = [r for r in rr if r]
        if rr:
            fhir["reasonReference"] = rr

    if payload.managing_organization:
        mo = [_child_reference_from_payload(m) for m in payload.managing_organization]
        mo = [m for m in mo if m]
        if mo:
            fhir["managingOrganization"] = mo

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


_SUBJECT_FIELDS = {"subject", "subject_display"} | {f"subject_{s}" for s in _IDENTIFIER_FALLBACK_SUFFIXES}
_ENCOUNTER_FIELDS = {"encounter", "encounter_display"} | {f"encounter_{s}" for s in _IDENTIFIER_FALLBACK_SUFFIXES}


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

    if fields_set & _SUBJECT_FIELDS:
        touched.add("subject")
        subj = _reference_from_payload(payload, "subject")
        if subj:
            fragment["subject"] = subj

    if fields_set & _ENCOUNTER_FIELDS:
        touched.add("encounter")
        enc = _reference_from_payload(payload, "encounter")
        if enc:
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
            fragment["reasonReference"] = [
                _child_reference_from_payload(r) for r in payload.reason_reference if _child_reference_from_payload(r)
            ]

    if "managing_organization" in fields_set:
        touched.add("managingOrganization")
        if payload.managing_organization is not None:
            fragment["managingOrganization"] = [
                _child_reference_from_payload(m) for m in payload.managing_organization if _child_reference_from_payload(m)
            ]

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
