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


def _fhir_participant(p: CareTeamParticipant) -> dict:
    result: dict[str, Any] = {}
    if p.roles:
        roles_fhir = [_fhir_codeable_concept(r.codings, r.text) for r in p.roles]
        roles_fhir = [r for r in roles_fhir if r]
        if roles_fhir:
            result["role"] = roles_fhir
    member = _fhir_reference(p, "member")
    if member:
        result["member"] = member
    on_behalf_of = _fhir_reference(p, "on_behalf_of")
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


def to_fhir_care_team(model: CareTeamModel) -> dict[str, Any]:
    """Serialize a CareTeamModel instance to FHIR R4 CareTeam JSON dict."""
    fhir: dict[str, Any] = {
        "resourceType": "CareTeam",
        "id": str(model.care_team_id),
    }

    # Meta
    meta: dict[str, Any] = {
        "versionId": str(model.version_id) if hasattr(model, "version_id") and model.version_id else "1",
    }
    if model.updated_at:
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    elif model.created_at:
        meta["lastUpdated"] = fhir_instant(model.created_at)
    fhir["meta"] = meta

    # Extension
    if model.extension:
        fhir["extension"] = model.extension

    # status
    if model.status:
        fhir["status"] = fhir_enum(model.status)

    # name
    if model.name:
        fhir["name"] = model.name

    # subject
    subject = _fhir_reference(model, "subject")
    if subject:
        fhir["subject"] = subject

    # encounter
    encounter = _fhir_reference(model, "encounter")
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
        rr = [_fhir_reference(r, "reference") for r in model.reason_references]
        rr = [r for r in rr if r]
        if rr:
            fhir["reasonReference"] = rr

    # managingOrganization
    if model.managing_organizations:
        mo = [_fhir_reference(m, "reference") for m in model.managing_organizations]
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
            assigner = _fhir_reference(i, "assigner")
            if assigner:
                ident_obj["assigner"] = assigner
            if ident_obj:
                identifiers.append(ident_obj)
        if identifiers:
            fhir["identifier"] = identifiers

    return fhir
