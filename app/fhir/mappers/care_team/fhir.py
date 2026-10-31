from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.care_team import CareTeamModel, CareTeamParticipant


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


def _fhir_participant(p: CareTeamParticipant) -> dict:
    result: dict[str, Any] = {}
    if p.roles:
        roles_fhir = [_fhir_codeable_concept(r.codings, r.text) for r in p.roles]
        roles_fhir = [r for r in roles_fhir if r]
        if roles_fhir:
            result["role"] = roles_fhir
    member = _fhir_ref(p.member_reference, p.member_type, p.member_id, p.member_display)
    if member:
        result["member"] = member
    on_behalf_of = _fhir_ref(p.on_behalf_of_reference, p.on_behalf_of_type, p.on_behalf_of_id, p.on_behalf_of_display)
    if on_behalf_of:
        result["onBehalfOf"] = on_behalf_of
    period = _fhir_period(p.period_start, p.period_end)
    if period:
        result["period"] = period
    return result


def _fhir_telecom(t) -> dict:
    result: dict[str, Any] = {}
    if t.system:
        result["system"] = fhir_enum(t.system)
    if t.value:
        result["value"] = t.value
    if t.use:
        result["use"] = fhir_enum(t.use)
    if t.rank is not None:
        result["rank"] = t.rank
    period = _fhir_period(t.period_start, t.period_end)
    if period:
        result["period"] = period
    return result


def _fhir_meta(model: CareTeamModel) -> dict:
    meta: dict[str, Any] = {}
    last_updated = model.updated_at or model.created_at
    if last_updated:
        meta["lastUpdated"] = fhir_instant(last_updated)
    return meta


def to_fhir_care_team(model: CareTeamModel) -> dict:
    """Convert CareTeamModel to full FHIR R4 CareTeam resource JSON."""
    fhir: dict[str, Any] = {
        "resourceType": "CareTeam",
        "id": str(model.care_team_id),
    }

    meta = _fhir_meta(model)
    if meta:
        fhir["meta"] = meta

    if model.extension:
        fhir["extension"] = model.extension

    # status
    if model.status:
        fhir["status"] = fhir_enum(model.status)

    # name
    if model.name:
        fhir["name"] = model.name

    # subject
    subject = _fhir_ref(model.subject_reference, model.subject_type, model.subject_id, model.subject_display)
    if subject:
        fhir["subject"] = subject

    # encounter
    encounter = _fhir_ref(model.encounter_reference, model.encounter_type, model.encounter_id, model.encounter_display)
    if encounter:
        fhir["encounter"] = encounter

    # period
    period = _fhir_period(model.period_start, model.period_end)
    if period:
        fhir["period"] = period

    # category
    if model.categories:
        cats = [_fhir_codeable_concept(c.codings, c.text) for c in model.categories]
        cats = [c for c in cats if c]
        if cats:
            fhir["category"] = cats

    # participant
    if model.participants:
        participants = [_fhir_participant(p) for p in model.participants]
        participants = [p for p in participants if p]
        if participants:
            fhir["participant"] = participants

    # reasonCode
    if model.reason_codes:
        reasons = [_fhir_codeable_concept(r.codings, r.text) for r in model.reason_codes]
        reasons = [r for r in reasons if r]
        if reasons:
            fhir["reasonCode"] = reasons

    # reasonReference
    if model.reason_references:
        rr = [_fhir_ref(r.reference_reference, r.reference_type, r.reference_id, r.reference_display) for r in model.reason_references]
        rr = [r for r in rr if r]
        if rr:
            fhir["reasonReference"] = rr

    # managingOrganization
    if model.managing_organizations:
        mo = [_fhir_ref(m.reference_reference, m.reference_type, m.reference_id, m.reference_display) for m in model.managing_organizations]
        mo = [m for m in mo if m]
        if mo:
            fhir["managingOrganization"] = mo

    # telecom
    if model.telecoms:
        telecoms = [_fhir_telecom(t) for t in model.telecoms]
        telecoms = [t for t in telecoms if t]
        if telecoms:
            fhir["telecom"] = telecoms

    # note
    if model.notes:
        notes = []
        for n in model.notes:
            note_obj: dict[str, Any] = {"text": n.text}
            if n.time:
                note_obj["time"] = fhir_instant(n.time)
            if n.author_string:
                note_obj["authorString"] = n.author_string
            author_ref = _fhir_ref(n.author_reference_reference, n.author_reference_type, n.author_reference_id, n.author_reference_display)
            if author_ref:
                note_obj["authorReference"] = author_ref
            notes.append(note_obj)
        if notes:
            fhir["note"] = notes

    # identifier
    if model.identifiers:
        identifiers = []
        for i in model.identifiers:
            ident_obj: dict[str, Any] = {}
            if i.use:
                ident_obj["use"] = fhir_enum(i.use)
            t_cc = _fhir_codeable_concept(i.type_codings, i.type_text)
            if t_cc:
                ident_obj["type"] = t_cc
            if i.system:
                ident_obj["system"] = i.system
            if i.value:
                ident_obj["value"] = i.value
            p = _fhir_period(i.period_start, i.period_end)
            if p:
                ident_obj["period"] = p
            assigner = _fhir_reference_with_identifier_fallback(i, "assigner")
            if assigner:
                ident_obj["assigner"] = assigner
            if ident_obj:
                identifiers.append(ident_obj)
        if identifiers:
            fhir["identifier"] = identifiers

    return fhir
