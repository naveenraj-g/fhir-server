"""Payload -> FHIR JSON conversion for Procedure.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(ProcedureCreateSchema / ProcedurePatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.schemas.procedure.input import (
        ProcedureCodeableConceptInput,
        ProcedureCreateSchema,
        ProcedureFocalDeviceInput,
        ProcedureIdentifierInput,
        ProcedureNoteInput,
        ProcedurePatchSchema,
        ProcedurePerformerInput,
    )


def _coding_from_payload(c: Any) -> dict:
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
    concept: ProcedureCodeableConceptInput | dict | None,
) -> dict | None:
    if not concept:
        return None
    if isinstance(concept, dict):
        codings = [_coding_from_payload(c) for c in (concept.get("coding") or [])]
        codings = [c for c in codings if c]
        text = concept.get("text")
    else:
        codings = [_coding_from_payload(c) for c in (concept.coding or [])]
        codings = [c for c in codings if c]
        text = concept.text

    result: dict = {}
    if codings:
        result["coding"] = codings
    if text:
        result["text"] = text
    return result or None


def _identifier_from_payload(
    ident: ProcedureIdentifierInput | dict | None,
) -> dict | None:
    if not ident:
        return None
    entry: dict = {}
    if isinstance(ident, dict):
        use = ident.get("use")
        type_in = ident.get("type")
        system = ident.get("system")
        value = ident.get("value")
        p_start = ident.get("period_start")
        p_end = ident.get("period_end")
        assigner = ident.get("assigner")
        assigner_disp = ident.get("assigner_display")
    else:
        use = ident.use
        type_in = ident.type
        system = ident.system
        value = ident.value
        p_start = ident.period_start
        p_end = ident.period_end
        assigner = ident.assigner
        assigner_disp = ident.assigner_display

    if use:
        entry["use"] = fhir_enum(use)
    if type_in:
        type_cc = _codeable_concept_from_payload(type_in)
        if type_cc:
            entry["type"] = type_cc
    if system:
        entry["system"] = system
    if value:
        entry["value"] = value
    if p_start or p_end:
        period: dict = {}
        if p_start:
            period["start"] = p_start.isoformat() if hasattr(p_start, "isoformat") else str(p_start)
        if p_end:
            period["end"] = p_end.isoformat() if hasattr(p_end, "isoformat") else str(p_end)
        entry["period"] = period
    if assigner or assigner_disp:
        ass_entry: dict = {}
        if assigner:
            ass_entry["reference"] = assigner
        if assigner_disp:
            ass_entry["display"] = assigner_disp
        entry["assigner"] = ass_entry
    return entry or None


def _performer_from_payload(
    p: ProcedurePerformerInput | dict | None,
) -> dict | None:
    if not p:
        return None
    if isinstance(p, dict):
        fn = p.get("function")
        actor = p.get("actor")
        actor_disp = p.get("actor_display")
        on_behalf = p.get("on_behalf_of")
        on_behalf_disp = p.get("on_behalf_of_display")
    else:
        fn = p.function
        actor = p.actor
        actor_disp = p.actor_display
        on_behalf = p.on_behalf_of
        on_behalf_disp = p.on_behalf_of_display

    entry: dict = {}
    fn_cc = _codeable_concept_from_payload(fn)
    if fn_cc:
        entry["function"] = fn_cc
    if actor or actor_disp:
        actor_dict: dict = {}
        if actor:
            actor_dict["reference"] = actor
        if actor_disp:
            actor_dict["display"] = actor_disp
        entry["actor"] = actor_dict
    if on_behalf or on_behalf_disp:
        ob_dict: dict = {}
        if on_behalf:
            ob_dict["reference"] = on_behalf
        if on_behalf_disp:
            ob_dict["display"] = on_behalf_disp
        entry["onBehalfOf"] = ob_dict
    return entry or None


def _focal_device_from_payload(
    d: ProcedureFocalDeviceInput | dict | None,
) -> dict | None:
    if not d:
        return None
    if isinstance(d, dict):
        act = d.get("action")
        man = d.get("manipulated")
        man_disp = d.get("manipulated_display")
    else:
        act = d.action
        man = d.manipulated
        man_disp = d.manipulated_display

    entry: dict = {}
    act_cc = _codeable_concept_from_payload(act)
    if act_cc:
        entry["action"] = act_cc
    if man or man_disp:
        man_dict: dict = {}
        if man:
            man_dict["reference"] = man
        if man_disp:
            man_dict["display"] = man_disp
        entry["manipulated"] = man_dict
    return entry or None


def _note_from_payload(
    n: ProcedureNoteInput | dict | None,
) -> dict | None:
    if not n:
        return None
    if isinstance(n, dict):
        auth_str = n.get("author_string")
        auth_ref = n.get("author_reference")
        auth_disp = n.get("author_reference_display")
        time_val = n.get("time")
        text_val = n.get("text")
    else:
        auth_str = n.author_string
        auth_ref = n.author_reference
        auth_disp = n.author_reference_display
        time_val = n.time
        text_val = n.text

    entry: dict = {}
    if auth_ref or auth_disp:
        ar_dict: dict = {}
        if auth_ref:
            ar_dict["reference"] = auth_ref
        if auth_disp:
            ar_dict["display"] = auth_disp
        entry["authorReference"] = ar_dict
    elif auth_str:
        entry["authorString"] = auth_str

    if time_val:
        entry["time"] = time_val.isoformat() if hasattr(time_val, "isoformat") else str(time_val)
    if text_val:
        entry["text"] = text_val
    return entry or None


def payload_to_fhir_procedure(payload: ProcedureCreateSchema) -> dict:
    """Map ProcedureCreateSchema to base FHIR R4 JSON dict for validation."""
    res: dict[str, Any] = {
        "resourceType": "Procedure",
        "id": "placeholder-procedure-id",
    }

    if payload.identifier:
        ident_list = [_identifier_from_payload(i) for i in payload.identifier]
        ident_list = [i for i in ident_list if i]
        if ident_list:
            res["identifier"] = ident_list

    if payload.instantiates_canonical:
        res["instantiatesCanonical"] = list(payload.instantiates_canonical)

    if payload.instantiates_uri:
        res["instantiatesUri"] = list(payload.instantiates_uri)

    if payload.based_on:
        res["basedOn"] = [{"reference": r} for r in payload.based_on if r]

    if payload.part_of:
        res["partOf"] = [{"reference": r} for r in payload.part_of if r]

    if payload.status:
        res["status"] = fhir_enum(payload.status)

    if payload.status_reason:
        sr = _codeable_concept_from_payload(payload.status_reason)
        if sr:
            res["statusReason"] = sr

    if payload.category:
        cat = _codeable_concept_from_payload(payload.category)
        if cat:
            res["category"] = cat

    if payload.code:
        code = _codeable_concept_from_payload(payload.code)
        if code:
            res["code"] = code

    if payload.subject:
        subj: dict = {"reference": payload.subject}
        if payload.subject_display:
            subj["display"] = payload.subject_display
        res["subject"] = subj

    if payload.encounter or payload.encounter_display:
        enc: dict = {}
        if payload.encounter:
            enc["reference"] = payload.encounter
        if payload.encounter_display:
            enc["display"] = payload.encounter_display
        res["encounter"] = enc

    if payload.performed_date_time:
        res["performedDateTime"] = (
            payload.performed_date_time.isoformat()
            if hasattr(payload.performed_date_time, "isoformat")
            else str(payload.performed_date_time)
        )
    elif payload.performed_period_start or payload.performed_period_end:
        period: dict = {}
        if payload.performed_period_start:
            period["start"] = (
                payload.performed_period_start.isoformat()
                if hasattr(payload.performed_period_start, "isoformat")
                else str(payload.performed_period_start)
            )
        if payload.performed_period_end:
            period["end"] = (
                payload.performed_period_end.isoformat()
                if hasattr(payload.performed_period_end, "isoformat")
                else str(payload.performed_period_end)
            )
        res["performedPeriod"] = period
    elif payload.performed_string:
        res["performedString"] = payload.performed_string
    elif payload.performed_age:
        res["performedAge"] = payload.performed_age
    elif payload.performed_range:
        res["performedRange"] = payload.performed_range

    if payload.recorder or payload.recorder_display:
        rec: dict = {}
        if payload.recorder:
            rec["reference"] = payload.recorder
        if payload.recorder_display:
            rec["display"] = payload.recorder_display
        res["recorder"] = rec

    if payload.asserter or payload.asserter_display:
        ass: dict = {}
        if payload.asserter:
            ass["reference"] = payload.asserter
        if payload.asserter_display:
            ass["display"] = payload.asserter_display
        res["asserter"] = ass

    if payload.performer:
        perf_list = [_performer_from_payload(p) for p in payload.performer]
        perf_list = [p for p in perf_list if p]
        if perf_list:
            res["performer"] = perf_list

    if payload.location or payload.location_display:
        loc: dict = {}
        if payload.location:
            loc["reference"] = payload.location
        if payload.location_display:
            loc["display"] = payload.location_display
        res["location"] = loc

    if payload.reason_code:
        rc_list = [_codeable_concept_from_payload(rc) for rc in payload.reason_code]
        rc_list = [rc for rc in rc_list if rc]
        if rc_list:
            res["reasonCode"] = rc_list

    if payload.reason_reference:
        res["reasonReference"] = [{"reference": r} for r in payload.reason_reference if r]

    if payload.body_site:
        bs_list = [_codeable_concept_from_payload(bs) for bs in payload.body_site]
        bs_list = [bs for bs in bs_list if bs]
        if bs_list:
            res["bodySite"] = bs_list

    if payload.outcome:
        out = _codeable_concept_from_payload(payload.outcome)
        if out:
            res["outcome"] = out

    if payload.report:
        res["report"] = [{"reference": r} for r in payload.report if r]

    if payload.complication:
        comp_list = [_codeable_concept_from_payload(c) for c in payload.complication]
        comp_list = [c for c in comp_list if c]
        if comp_list:
            res["complication"] = comp_list

    if payload.complication_detail:
        res["complicationDetail"] = [{"reference": r} for r in payload.complication_detail if r]

    if payload.follow_up:
        fu_list = [_codeable_concept_from_payload(fu) for fu in payload.follow_up]
        fu_list = [fu for fu in fu_list if fu]
        if fu_list:
            res["followUp"] = fu_list

    if payload.note:
        n_list = [_note_from_payload(n) for n in payload.note]
        n_list = [n for n in n_list if n]
        if n_list:
            res["note"] = n_list

    if payload.focal_device:
        fd_list = [_focal_device_from_payload(d) for d in payload.focal_device]
        fd_list = [d for d in fd_list if d]
        if fd_list:
            res["focalDevice"] = fd_list

    if payload.used_reference:
        res["usedReference"] = [{"reference": r} for r in payload.used_reference if r]

    if payload.used_code:
        uc_list = [_codeable_concept_from_payload(uc) for uc in payload.used_code]
        uc_list = [uc for uc in uc_list if uc]
        if uc_list:
            res["usedCode"] = uc_list

    if payload.extension:
        res["extension"] = payload.extension

    return {k: v for k, v in res.items() if v is not None}


def patch_fragment_to_fhir_procedure(
    payload: ProcedurePatchSchema,
) -> tuple[dict, set[str]]:
    """Map touched fields of ProcedurePatchSchema to a partial FHIR dict and set of touched keys."""
    touched: set[str] = set()
    fragment: dict = {}
    fields_set = payload.model_fields_set

    if "identifier" in fields_set:
        touched.add("identifier")
        if payload.identifier is not None:
            fragment["identifier"] = [
                i for i in [_identifier_from_payload(x) for x in payload.identifier] if i
            ]

    if "instantiates_canonical" in fields_set:
        touched.add("instantiatesCanonical")
        if payload.instantiates_canonical is not None:
            fragment["instantiatesCanonical"] = list(payload.instantiates_canonical)

    if "instantiates_uri" in fields_set:
        touched.add("instantiatesUri")
        if payload.instantiates_uri is not None:
            fragment["instantiatesUri"] = list(payload.instantiates_uri)

    if "based_on" in fields_set:
        touched.add("basedOn")
        if payload.based_on is not None:
            fragment["basedOn"] = [{"reference": r} for r in payload.based_on if r]

    if "part_of" in fields_set:
        touched.add("partOf")
        if payload.part_of is not None:
            fragment["partOf"] = [{"reference": r} for r in payload.part_of if r]

    if "status" in fields_set:
        touched.add("status")
        if payload.status is not None:
            fragment["status"] = fhir_enum(payload.status)

    if "status_reason" in fields_set:
        touched.add("statusReason")
        if payload.status_reason is not None:
            fragment["statusReason"] = _codeable_concept_from_payload(payload.status_reason)

    if "category" in fields_set:
        touched.add("category")
        if payload.category is not None:
            fragment["category"] = _codeable_concept_from_payload(payload.category)

    if "code" in fields_set:
        touched.add("code")
        if payload.code is not None:
            fragment["code"] = _codeable_concept_from_payload(payload.code)

    if "subject" in fields_set or "subject_display" in fields_set:
        touched.add("subject")
        if payload.subject is not None:
            subj: dict = {"reference": payload.subject}
            if payload.subject_display:
                subj["display"] = payload.subject_display
            fragment["subject"] = subj

    if "encounter" in fields_set or "encounter_display" in fields_set:
        touched.add("encounter")
        if payload.encounter is not None or payload.encounter_display is not None:
            enc: dict = {}
            if payload.encounter:
                enc["reference"] = payload.encounter
            if payload.encounter_display:
                enc["display"] = payload.encounter_display
            fragment["encounter"] = enc

    # performed[x] fields
    performed_keys = {
        "performed_date_time",
        "performed_period_start",
        "performed_period_end",
        "performed_string",
        "performed_age",
        "performed_range",
    }
    if performed_keys & fields_set:
        touched.update(
            [
                "performedDateTime",
                "performedPeriod",
                "performedString",
                "performedAge",
                "performedRange",
            ]
        )
        if payload.performed_date_time is not None:
            fragment["performedDateTime"] = (
                payload.performed_date_time.isoformat()
                if hasattr(payload.performed_date_time, "isoformat")
                else str(payload.performed_date_time)
            )
        elif payload.performed_period_start or payload.performed_period_end:
            period: dict = {}
            if payload.performed_period_start:
                period["start"] = (
                    payload.performed_period_start.isoformat()
                    if hasattr(payload.performed_period_start, "isoformat")
                    else str(payload.performed_period_start)
                )
            if payload.performed_period_end:
                period["end"] = (
                    payload.performed_period_end.isoformat()
                    if hasattr(payload.performed_period_end, "isoformat")
                    else str(payload.performed_period_end)
                )
            fragment["performedPeriod"] = period
        elif payload.performed_string is not None:
            fragment["performedString"] = payload.performed_string
        elif payload.performed_age is not None:
            fragment["performedAge"] = payload.performed_age
        elif payload.performed_range is not None:
            fragment["performedRange"] = payload.performed_range

    if "recorder" in fields_set or "recorder_display" in fields_set:
        touched.add("recorder")
        if payload.recorder is not None or payload.recorder_display is not None:
            rec: dict = {}
            if payload.recorder:
                rec["reference"] = payload.recorder
            if payload.recorder_display:
                rec["display"] = payload.recorder_display
            fragment["recorder"] = rec

    if "asserter" in fields_set or "asserter_display" in fields_set:
        touched.add("asserter")
        if payload.asserter is not None or payload.asserter_display is not None:
            ass: dict = {}
            if payload.asserter:
                ass["reference"] = payload.asserter
            if payload.asserter_display:
                ass["display"] = payload.asserter_display
            fragment["asserter"] = ass

    if "performer" in fields_set:
        touched.add("performer")
        if payload.performer is not None:
            fragment["performer"] = [
                p for p in [_performer_from_payload(x) for x in payload.performer] if p
            ]

    if "location" in fields_set or "location_display" in fields_set:
        touched.add("location")
        if payload.location is not None or payload.location_display is not None:
            loc: dict = {}
            if payload.location:
                loc["reference"] = payload.location
            if payload.location_display:
                loc["display"] = payload.location_display
            fragment["location"] = loc

    if "reason_code" in fields_set:
        touched.add("reasonCode")
        if payload.reason_code is not None:
            fragment["reasonCode"] = [
                rc for rc in [_codeable_concept_from_payload(x) for x in payload.reason_code] if rc
            ]

    if "reason_reference" in fields_set:
        touched.add("reasonReference")
        if payload.reason_reference is not None:
            fragment["reasonReference"] = [
                {"reference": r} for r in payload.reason_reference if r
            ]

    if "body_site" in fields_set:
        touched.add("bodySite")
        if payload.body_site is not None:
            fragment["bodySite"] = [
                bs for bs in [_codeable_concept_from_payload(x) for x in payload.body_site] if bs
            ]

    if "outcome" in fields_set:
        touched.add("outcome")
        if payload.outcome is not None:
            fragment["outcome"] = _codeable_concept_from_payload(payload.outcome)

    if "report" in fields_set:
        touched.add("report")
        if payload.report is not None:
            fragment["report"] = [{"reference": r} for r in payload.report if r]

    if "complication" in fields_set:
        touched.add("complication")
        if payload.complication is not None:
            fragment["complication"] = [
                c for c in [_codeable_concept_from_payload(x) for x in payload.complication] if c
            ]

    if "complication_detail" in fields_set:
        touched.add("complicationDetail")
        if payload.complication_detail is not None:
            fragment["complicationDetail"] = [
                {"reference": r} for r in payload.complication_detail if r
            ]

    if "follow_up" in fields_set:
        touched.add("followUp")
        if payload.follow_up is not None:
            fragment["followUp"] = [
                fu for fu in [_codeable_concept_from_payload(x) for x in payload.follow_up] if fu
            ]

    if "note" in fields_set:
        touched.add("note")
        if payload.note is not None:
            fragment["note"] = [
                n for n in [_note_from_payload(x) for x in payload.note] if n
            ]

    if "focal_device" in fields_set:
        touched.add("focalDevice")
        if payload.focal_device is not None:
            fragment["focalDevice"] = [
                d for d in [_focal_device_from_payload(x) for x in payload.focal_device] if d
            ]

    if "used_reference" in fields_set:
        touched.add("usedReference")
        if payload.used_reference is not None:
            fragment["usedReference"] = [
                {"reference": r} for r in payload.used_reference if r
            ]

    if "used_code" in fields_set:
        touched.add("usedCode")
        if payload.used_code is not None:
            fragment["usedCode"] = [
                uc for uc in [_codeable_concept_from_payload(x) for x in payload.used_code] if uc
            ]

    if "extension" in fields_set:
        touched.add("extension")
        if payload.extension is not None:
            fragment["extension"] = payload.extension

    return fragment, touched
