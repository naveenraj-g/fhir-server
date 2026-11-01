"""Payload -> FHIR JSON conversion for Procedure.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(ProcedureCreateSchema / ProcedurePatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, merge_patch_fragment
from app.repository._reference_shared import _IDENTIFIER_FALLBACK_SUFFIXES

if TYPE_CHECKING:
    from app.schemas.procedure.input import (
        ProcedureCodeableConceptInput,
        ProcedureCreateSchema,
        ProcedureFocalDeviceInput,
        ProcedureIdentifierInput,
        ProcedureNoteInput,
        ProcedurePatchSchema,
        ProcedurePerformerInput,
        ProcedureReferenceInput,
    )

_SUBJECT_FIELDS = {"subject", "subject_display"} | {
    f"subject_{s}" for s in _IDENTIFIER_FALLBACK_SUFFIXES
}
_ENCOUNTER_FIELDS = {"encounter", "encounter_display"} | {
    f"encounter_{s}" for s in _IDENTIFIER_FALLBACK_SUFFIXES
}
_RECORDER_FIELDS = {"recorder", "recorder_display"} | {
    f"recorder_{s}" for s in _IDENTIFIER_FALLBACK_SUFFIXES
}
_ASSERTER_FIELDS = {"asserter", "asserter_display"} | {
    f"asserter_{s}" for s in _IDENTIFIER_FALLBACK_SUFFIXES
}
_LOCATION_FIELDS = {"location", "location_display"} | {
    f"location_{s}" for s in _IDENTIFIER_FALLBACK_SUFFIXES
}


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
    id_type_user_selected = _get(f"{prefix}_identifier_type_user_selected") if _get(f"{prefix}_identifier_type_user_selected") is not None else _get("identifier_type_user_selected")
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


def _identifier_from_payload(
    ident: ProcedureIdentifierInput | dict | None,
) -> dict | None:
    if not ident:
        return None
    entry: dict = {}
    if isinstance(ident, dict):
        use = ident.get("use")
        type_coding = ident.get("type_coding")
        type_text = ident.get("type_text")
        type_in = ident.get("type")
        system = ident.get("system")
        value = ident.get("value")
        p_start = ident.get("period_start")
        p_end = ident.get("period_end")
    else:
        use = ident.use
        type_coding = getattr(ident, "type_coding", None)
        type_text = getattr(ident, "type_text", None)
        type_in = getattr(ident, "type", None)
        system = ident.system
        value = ident.value
        p_start = ident.period_start
        p_end = ident.period_end

    if use:
        entry["use"] = fhir_enum(use)
    if type_in:
        type_cc = _codeable_concept_from_payload(type_in)
        if type_cc:
            entry["type"] = type_cc
    elif type_coding or type_text:
        cc: dict = {}
        if type_coding:
            cc["coding"] = [_coding_from_payload(c) for c in type_coding if _coding_from_payload(c)]
        if type_text:
            cc["text"] = type_text
        if cc:
            entry["type"] = cc
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

    assigner = _reference_from_payload(ident, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _performer_from_payload(
    p: ProcedurePerformerInput | dict | None,
) -> dict | None:
    if not p:
        return None
    if isinstance(p, dict):
        fn = p.get("function")
    else:
        fn = p.function

    entry: dict = {}
    fn_cc = _codeable_concept_from_payload(fn)
    if fn_cc:
        entry["function"] = fn_cc

    actor = _reference_from_payload(p, "actor")
    if actor:
        entry["actor"] = actor

    on_behalf = _reference_from_payload(p, "on_behalf_of")
    if on_behalf:
        entry["onBehalfOf"] = on_behalf
    return entry or None


def _focal_device_from_payload(
    d: ProcedureFocalDeviceInput | dict | None,
) -> dict | None:
    if not d:
        return None
    if isinstance(d, dict):
        act = d.get("action")
    else:
        act = d.action

    entry: dict = {}
    act_cc = _codeable_concept_from_payload(act)
    if act_cc:
        entry["action"] = act_cc

    manipulated = _reference_from_payload(d, "manipulated")
    if manipulated:
        entry["manipulated"] = manipulated
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
        b_list = [_child_reference_from_payload(r) for r in payload.based_on]
        res["basedOn"] = [b for b in b_list if b]

    if payload.part_of:
        p_list = [_child_reference_from_payload(r) for r in payload.part_of]
        res["partOf"] = [p for p in p_list if p]

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

    subject = _reference_from_payload(payload, "subject")
    if subject:
        res["subject"] = subject

    encounter = _reference_from_payload(payload, "encounter")
    if encounter:
        res["encounter"] = encounter

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

    recorder = _reference_from_payload(payload, "recorder")
    if recorder:
        res["recorder"] = recorder

    asserter = _reference_from_payload(payload, "asserter")
    if asserter:
        res["asserter"] = asserter

    if payload.performer:
        perf_list = [_performer_from_payload(p) for p in payload.performer]
        perf_list = [p for p in perf_list if p]
        if perf_list:
            res["performer"] = perf_list

    location = _reference_from_payload(payload, "location")
    if location:
        res["location"] = location

    if payload.reason_code:
        rc_list = [_codeable_concept_from_payload(rc) for rc in payload.reason_code]
        rc_list = [rc for rc in rc_list if rc]
        if rc_list:
            res["reasonCode"] = rc_list

    if payload.reason_reference:
        rr_list = [_child_reference_from_payload(r) for r in payload.reason_reference]
        res["reasonReference"] = [rr for rr in rr_list if rr]

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
        rep_list = [_child_reference_from_payload(r) for r in payload.report]
        res["report"] = [r for r in rep_list if r]

    if payload.complication:
        comp_list = [_codeable_concept_from_payload(c) for c in payload.complication]
        comp_list = [c for c in comp_list if c]
        if comp_list:
            res["complication"] = comp_list

    if payload.complication_detail:
        cd_list = [_child_reference_from_payload(r) for r in payload.complication_detail]
        res["complicationDetail"] = [cd for cd in cd_list if cd]

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
        ur_list = [_child_reference_from_payload(r) for r in payload.used_reference]
        res["usedReference"] = [ur for ur in ur_list if ur]

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
            fragment["basedOn"] = [
                b for b in [_child_reference_from_payload(r) for r in payload.based_on] if b
            ]

    if "part_of" in fields_set:
        touched.add("partOf")
        if payload.part_of is not None:
            fragment["partOf"] = [
                p for p in [_child_reference_from_payload(r) for r in payload.part_of] if p
            ]

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

    if fields_set & _RECORDER_FIELDS:
        touched.add("recorder")
        rec = _reference_from_payload(payload, "recorder")
        if rec:
            fragment["recorder"] = rec

    if fields_set & _ASSERTER_FIELDS:
        touched.add("asserter")
        ass = _reference_from_payload(payload, "asserter")
        if ass:
            fragment["asserter"] = ass

    if "performer" in fields_set:
        touched.add("performer")
        if payload.performer is not None:
            fragment["performer"] = [
                p for p in [_performer_from_payload(x) for x in payload.performer] if p
            ]

    if fields_set & _LOCATION_FIELDS:
        touched.add("location")
        loc = _reference_from_payload(payload, "location")
        if loc:
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
                rr for rr in [_child_reference_from_payload(r) for r in payload.reason_reference] if rr
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
            fragment["report"] = [
                rep for rep in [_child_reference_from_payload(r) for r in payload.report] if rep
            ]

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
                cd for cd in [_child_reference_from_payload(r) for r in payload.complication_detail] if cd
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
                ur for ur in [_child_reference_from_payload(r) for r in payload.used_reference] if ur
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
