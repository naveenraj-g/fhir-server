from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.procedure import (
        ProcedureFocalDevice,
        ProcedureIdentifier,
        ProcedureModel,
        ProcedureNote,
        ProcedurePerformer,
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


def _fhir_ref(
    ref_raw: str | None,
    ref_type: Any,
    ref_id: int | None,
    display: str | None,
) -> dict | None:
    result: dict = {}
    if ref_raw:
        result["reference"] = ref_raw
    elif ref_type and ref_id:
        result["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        result["display"] = display
    return result or None


def _fhir_identifier(i: ProcedureIdentifier) -> dict | None:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    type_cc = _fhir_codeable_concept(getattr(i, "type_codings", None), i.type_text)
    if type_cc:
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    if i.period_start or i.period_end:
        period: dict = {}
        if i.period_start:
            period["start"] = fhir_instant(i.period_start)
        if i.period_end:
            period["end"] = fhir_instant(i.period_end)
        entry["period"] = period
    assigner = _fhir_ref(
        i.assigner_reference,
        i.assigner_type,
        i.assigner_id,
        i.assigner_display,
    )
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _fhir_performer(p: ProcedurePerformer) -> dict | None:
    entry: dict = {}
    fn_cc = _fhir_codeable_concept(getattr(p, "function_codings", None), p.function_text)
    if fn_cc:
        entry["function"] = fn_cc
    actor = _fhir_ref(p.actor_reference, p.actor_type, p.actor_id, p.actor_display)
    if actor:
        entry["actor"] = actor
    on_behalf = _fhir_ref(
        p.on_behalf_of_reference,
        p.on_behalf_of_type,
        p.on_behalf_of_id,
        p.on_behalf_of_display,
    )
    if on_behalf:
        entry["onBehalfOf"] = on_behalf
    return entry or None


def _fhir_focal_device(d: ProcedureFocalDevice) -> dict | None:
    entry: dict = {}
    action_cc = _fhir_codeable_concept(getattr(d, "action_codings", None), d.action_text)
    if action_cc:
        entry["action"] = action_cc
    manipulated = _fhir_ref(
        d.manipulated_reference,
        d.manipulated_type,
        d.manipulated_id,
        d.manipulated_display,
    )
    if manipulated:
        entry["manipulated"] = manipulated
    return entry or None


def _fhir_annotation(note: ProcedureNote) -> dict | None:
    entry: dict = {}
    author_ref = _fhir_ref(
        getattr(note, "author_reference_reference", None),
        getattr(note, "author_reference_type", None),
        getattr(note, "author_reference_id", None),
        getattr(note, "author_reference_display", None),
    )
    if author_ref:
        entry["authorReference"] = author_ref
    elif getattr(note, "author_string", None):
        entry["authorString"] = note.author_string
    if getattr(note, "time", None):
        entry["time"] = fhir_instant(note.time)
    if getattr(note, "text", None):
        entry["text"] = note.text
    return entry or None


def to_fhir_procedure(model: ProcedureModel) -> dict:
    """Map ProcedureModel ORM instance to FHIR R4 Procedure resource dict."""
    res: dict[str, Any] = {
        "resourceType": "Procedure",
        "id": str(model.procedure_id),
    }

    if model.updated_at:
        res["meta"] = {
            "versionId": "1",
            "lastUpdated": fhir_instant(model.updated_at),
        }

    if getattr(model, "identifiers", None):
        ident_list = [_fhir_identifier(i) for i in model.identifiers]
        ident_list = [i for i in ident_list if i]
        if ident_list:
            res["identifier"] = ident_list

    if model.instantiates_canonical:
        res["instantiatesCanonical"] = list(model.instantiates_canonical)

    if model.instantiates_uri:
        res["instantiatesUri"] = list(model.instantiates_uri)

    if getattr(model, "based_on", None):
        based_list = [
            _fhir_ref(b.reference_reference, b.reference_type, b.reference_id, b.reference_display)
            for b in model.based_on
        ]
        based_list = [b for b in based_list if b]
        if based_list:
            res["basedOn"] = based_list

    if getattr(model, "part_of", None):
        part_list = [
            _fhir_ref(p.reference_reference, p.reference_type, p.reference_id, p.reference_display)
            for p in model.part_of
        ]
        part_list = [p for p in part_list if p]
        if part_list:
            res["partOf"] = part_list

    if model.status:
        res["status"] = fhir_enum(model.status)

    status_reason = _fhir_codeable_concept(
        getattr(model, "status_reason_codings", None),
        model.status_reason_text,
    )
    if status_reason:
        res["statusReason"] = status_reason

    category = _fhir_codeable_concept(
        getattr(model, "category_codings", None),
        model.category_text,
    )
    if category:
        res["category"] = category

    code = _fhir_codeable_concept(
        getattr(model, "code_codings", None),
        model.code_text,
    )
    if code:
        res["code"] = code

    subject = _fhir_ref(
        model.subject_reference,
        model.subject_type,
        model.subject_id,
        model.subject_display,
    )
    if subject:
        res["subject"] = subject

    encounter = _fhir_ref(
        model.encounter_reference,
        model.encounter_type,
        model.encounter_id,
        model.encounter_display,
    )
    if encounter:
        res["encounter"] = encounter

    if model.performed_date_time:
        res["performedDateTime"] = fhir_instant(model.performed_date_time)
    elif model.performed_period_start or model.performed_period_end:
        period: dict = {}
        if model.performed_period_start:
            period["start"] = fhir_instant(model.performed_period_start)
        if model.performed_period_end:
            period["end"] = fhir_instant(model.performed_period_end)
        res["performedPeriod"] = period
    elif model.performed_string:
        res["performedString"] = model.performed_string
    elif model.performed_age:
        res["performedAge"] = model.performed_age
    elif model.performed_range:
        res["performedRange"] = model.performed_range

    recorder = _fhir_ref(
        model.recorder_reference,
        model.recorder_type,
        model.recorder_id,
        model.recorder_display,
    )
    if recorder:
        res["recorder"] = recorder

    asserter = _fhir_ref(
        model.asserter_reference,
        model.asserter_type,
        model.asserter_id,
        model.asserter_display,
    )
    if asserter:
        res["asserter"] = asserter

    if getattr(model, "performers", None):
        perf_list = [_fhir_performer(p) for p in model.performers]
        perf_list = [p for p in perf_list if p]
        if perf_list:
            res["performer"] = perf_list

    location = _fhir_ref(
        model.location_reference,
        model.location_type,
        model.location_id,
        model.location_display,
    )
    if location:
        res["location"] = location

    if getattr(model, "reason_codes", None):
        rc_list = [
            _fhir_codeable_concept(rc.codings, rc.text)
            for rc in model.reason_codes
        ]
        rc_list = [rc for rc in rc_list if rc]
        if rc_list:
            res["reasonCode"] = rc_list

    if getattr(model, "reason_references", None):
        rr_list = [
            _fhir_ref(rr.reference_reference, rr.reference_type, rr.reference_id, rr.reference_display)
            for rr in model.reason_references
        ]
        rr_list = [rr for rr in rr_list if rr]
        if rr_list:
            res["reasonReference"] = rr_list

    if getattr(model, "body_sites", None):
        bs_list = [
            _fhir_codeable_concept(bs.codings, bs.text)
            for bs in model.body_sites
        ]
        bs_list = [bs for bs in bs_list if bs]
        if bs_list:
            res["bodySite"] = bs_list

    outcome = _fhir_codeable_concept(
        getattr(model, "outcome_codings", None),
        model.outcome_text,
    )
    if outcome:
        res["outcome"] = outcome

    if getattr(model, "reports", None):
        rep_list = [
            _fhir_ref(r.reference_reference, r.reference_type, r.reference_id, r.reference_display)
            for r in model.reports
        ]
        rep_list = [r for r in rep_list if r]
        if rep_list:
            res["report"] = rep_list

    if getattr(model, "complications", None):
        comp_list = [
            _fhir_codeable_concept(c.codings, c.text)
            for c in model.complications
        ]
        comp_list = [c for c in comp_list if c]
        if comp_list:
            res["complication"] = comp_list

    if getattr(model, "complication_details", None):
        cd_list = [
            _fhir_ref(cd.reference_reference, cd.reference_type, cd.reference_id, cd.reference_display)
            for cd in model.complication_details
        ]
        cd_list = [cd for cd in cd_list if cd]
        if cd_list:
            res["complicationDetail"] = cd_list

    if getattr(model, "follow_ups", None):
        fu_list = [
            _fhir_codeable_concept(fu.codings, fu.text)
            for fu in model.follow_ups
        ]
        fu_list = [fu for fu in fu_list if fu]
        if fu_list:
            res["followUp"] = fu_list

    if getattr(model, "notes", None):
        note_list = [_fhir_annotation(n) for n in model.notes]
        note_list = [n for n in note_list if n]
        if note_list:
            res["note"] = note_list

    if getattr(model, "focal_devices", None):
        fd_list = [_fhir_focal_device(d) for d in model.focal_devices]
        fd_list = [d for d in fd_list if d]
        if fd_list:
            res["focalDevice"] = fd_list

    if getattr(model, "used_references", None):
        ur_list = [
            _fhir_ref(ur.reference_reference, ur.reference_type, ur.reference_id, ur.reference_display)
            for ur in model.used_references
        ]
        ur_list = [ur for ur in ur_list if ur]
        if ur_list:
            res["usedReference"] = ur_list

    if getattr(model, "used_codes", None):
        uc_list = [
            _fhir_codeable_concept(uc.codings, uc.text)
            for uc in model.used_codes
        ]
        uc_list = [uc for uc in uc_list if uc]
        if uc_list:
            res["usedCode"] = uc_list

    if model.extension:
        res["extension"] = model.extension

    return {k: v for k, v in res.items() if v is not None}
