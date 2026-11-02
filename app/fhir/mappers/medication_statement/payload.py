"""Payload -> FHIR JSON conversion for MedicationStatement.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(MedicationStatementCreateSchema / MedicationStatementPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import merge_patch_fragment

if TYPE_CHECKING:
    from app.schemas.medication_statement.input import (
        MedicationStatementCodeableConceptInput,
        MedicationStatementCreateSchema,
        MedicationStatementDosageInput,
        MedicationStatementIdentifierInput,
        MedicationStatementNoteInput,
        MedicationStatementPatchSchema,
        MedicationStatementReasonCodeInput,
        MedicationStatementStatusReasonInput,
    )

_MEDICATION_FIELDS = {"medication_codeable_concept", "medication_reference"}
_MEDICATION_FHIR_KEYS = {"medicationCodeableConcept", "medicationReference"}

_EFFECTIVE_FIELDS = {"effective_date_time", "effective_period_start", "effective_period_end"}
_EFFECTIVE_FHIR_KEYS = {"effectiveDateTime", "effectivePeriod"}


def _val(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _coding_from_payload(c: Any) -> dict:
    if isinstance(c, dict):
        return {
            k: v
            for k, v in {
                "system": c.get("system"),
                "version": c.get("version"),
                "code": c.get("code"),
                "display": c.get("display"),
                "userSelected": c.get("user_selected"),
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


def payload_medication_statement_codeable_concept(
    cc: MedicationStatementCodeableConceptInput | dict | None,
) -> dict | None:
    if not cc:
        return None
    coding_raw = _val(cc, "coding")
    codings = [_coding_from_payload(c) for c in (coding_raw or [])]
    codings = [c for c in codings if c]
    text = _val(cc, "text")

    result: dict = {}
    if codings:
        result["coding"] = codings
    if text:
        result["text"] = text
    return result or None


def _reference_with_identifier_from_payload(obj: Any) -> dict:
    if not obj:
        return {}
    ref = _val(obj, "reference")
    display = _val(obj, "reference_display") or _val(obj, "display")

    id_use = _val(obj, "reference_identifier_use") or _val(obj, "identifier_use")
    id_type_system = _val(obj, "reference_identifier_type_system") or _val(obj, "identifier_type_system")
    id_type_version = _val(obj, "reference_identifier_type_version") or _val(obj, "identifier_type_version")
    id_type_code = _val(obj, "reference_identifier_type_code") or _val(obj, "identifier_type_code")
    id_type_display = _val(obj, "reference_identifier_type_display") or _val(obj, "identifier_type_display")
    id_type_user_selected = _val(obj, "reference_identifier_type_user_selected") or _val(obj, "identifier_type_user_selected")
    id_type_text = _val(obj, "reference_identifier_type_text") or _val(obj, "identifier_type_text")
    id_system = _val(obj, "reference_identifier_system") or _val(obj, "identifier_system")
    id_value = _val(obj, "reference_identifier_value") or _val(obj, "identifier_value")
    id_period_start = _val(obj, "reference_identifier_period_start") or _val(obj, "identifier_period_start")
    id_period_end = _val(obj, "reference_identifier_period_end") or _val(obj, "identifier_period_end")

    entry: dict = {}
    if ref:
        entry["reference"] = ref
    if display:
        entry["display"] = display

    if (
        id_use
        or id_type_system
        or id_type_version
        or id_type_code
        or id_type_display
        or id_type_user_selected
        or id_type_text
        or id_system
        or id_value
        or id_period_start
        or id_period_end
    ):
        identifier: dict = {}
        if id_use:
            identifier["use"] = id_use.value if hasattr(id_use, "value") else str(id_use)
        if (
            id_type_system
            or id_type_code
            or id_type_text
            or id_type_display
            or id_type_version
            or id_type_user_selected
        ):
            type_cc: dict = {}
            if id_type_system or id_type_code or id_type_display or id_type_version or id_type_user_selected:
                type_cc["coding"] = [
                    {
                        k: v
                        for k, v in {
                            "system": id_type_system,
                            "version": id_type_version,
                            "code": id_type_code,
                            "display": id_type_display,
                            "userSelected": id_type_user_selected,
                        }.items()
                        if v is not None
                    }
                ]
            if id_type_text:
                type_cc["text"] = id_type_text
            identifier["type"] = type_cc
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        if id_period_start or id_period_end:
            identifier["period"] = {
                k: v
                for k, v in {
                    "start": id_period_start.isoformat() if hasattr(id_period_start, "isoformat") else (str(id_period_start) if id_period_start else None),
                    "end": id_period_end.isoformat() if hasattr(id_period_end, "isoformat") else (str(id_period_end) if id_period_end else None),
                }.items()
                if v is not None
            }
        if identifier:
            entry["identifier"] = identifier

    return entry


def payload_medication_statement_identifier(i: MedicationStatementIdentifierInput | dict) -> dict:
    res: dict = {}
    use = _val(i, "use")
    if use:
        res["use"] = use.value if hasattr(use, "value") else str(use)
    t = _val(i, "type")
    if t:
        type_cc = payload_medication_statement_codeable_concept(t)
        if type_cc:
            res["type"] = type_cc
    sys = _val(i, "system")
    if sys:
        res["system"] = sys
    val = _val(i, "value")
    if val:
        res["value"] = val
    start = _val(i, "period_start")
    end = _val(i, "period_end")
    if start or end:
        res["period"] = {
            k: v
            for k, v in {
                "start": start.isoformat() if hasattr(start, "isoformat") else (str(start) if start else None),
                "end": end.isoformat() if hasattr(end, "isoformat") else (str(end) if end else None),
            }.items()
            if v is not None
        }

    # Assigner fallback
    assigner_ref = _val(i, "assigner")
    assigner_display = _val(i, "assigner_display")
    if assigner_ref or assigner_display:
        assigner_dict: dict = {}
        if assigner_ref:
            assigner_dict["reference"] = assigner_ref
        if assigner_display:
            assigner_dict["display"] = assigner_display
        res["assigner"] = assigner_dict

    return {k: v for k, v in res.items() if v is not None}


def payload_medication_statement_status_reason(sr: MedicationStatementStatusReasonInput | dict) -> dict | None:
    return payload_medication_statement_codeable_concept(sr)


def payload_medication_statement_reason_code(rc: MedicationStatementReasonCodeInput | dict) -> dict | None:
    return payload_medication_statement_codeable_concept(rc)


def payload_medication_statement_note(n: MedicationStatementNoteInput | dict) -> dict:
    res: dict = {"text": _val(n, "text")}
    t = _val(n, "time")
    if t:
        res["time"] = t.isoformat() if hasattr(t, "isoformat") else str(t)
    auth_str = _val(n, "author_string")
    if auth_str:
        res["authorString"] = auth_str
    else:
        author_ref = _val(n, "author_reference")
        author_display = _val(n, "author_display")
        if author_ref or author_display:
            res["authorReference"] = {
                k: v
                for k, v in {
                    "reference": author_ref,
                    "display": author_display,
                }.items()
                if v is not None
            }
    return res


def _quantity_from_payload(obj: Any, prefix: str) -> dict | None:
    val = _val(obj, f"{prefix}_value")
    if val is None:
        return None
    res: dict = {"value": float(val)}
    unit = _val(obj, f"{prefix}_unit")
    system = _val(obj, f"{prefix}_system")
    code = _val(obj, f"{prefix}_code")
    if unit:
        res["unit"] = unit
    if system:
        res["system"] = system
    if code:
        res["code"] = code
    return res


def payload_medication_statement_dosage(d: MedicationStatementDosageInput | dict) -> dict:
    entry: dict = {}
    seq = _val(d, "sequence")
    if seq is not None:
        entry["sequence"] = seq
    txt = _val(d, "text")
    if txt:
        entry["text"] = txt
    add_instr = _val(d, "additional_instruction")
    if add_instr:
        ai_list = [payload_medication_statement_codeable_concept(ai) for ai in add_instr]
        ai_list = [ai for ai in ai_list if ai]
        if ai_list:
            entry["additionalInstruction"] = ai_list
    pat_instr = _val(d, "patient_instruction")
    if pat_instr:
        entry["patientInstruction"] = pat_instr
    tim = _val(d, "timing")
    if tim:
        entry["timing"] = dict(tim)

    as_needed_b = _val(d, "as_needed_boolean")
    if as_needed_b is not None:
        entry["asNeededBoolean"] = as_needed_b
    else:
        as_needed_cc = payload_medication_statement_codeable_concept(_val(d, "as_needed_codeable_concept"))
        if as_needed_cc:
            entry["asNeededCodeableConcept"] = as_needed_cc

    site = payload_medication_statement_codeable_concept(_val(d, "site"))
    if site:
        entry["site"] = site
    route = payload_medication_statement_codeable_concept(_val(d, "route"))
    if route:
        entry["route"] = route
    method = payload_medication_statement_codeable_concept(_val(d, "method"))
    if method:
        entry["method"] = method

    dnr = _val(d, "dose_and_rate")
    if dnr:
        entry["doseAndRate"] = list(dnr)
    mdpp = _val(d, "max_dose_per_period")
    if mdpp:
        entry["maxDosePerPeriod"] = dict(mdpp)

    mdpa = _quantity_from_payload(d, "max_dose_per_administration")
    if mdpa:
        entry["maxDosePerAdministration"] = mdpa
    mdpl = _quantity_from_payload(d, "max_dose_per_lifetime")
    if mdpl:
        entry["maxDosePerLifetime"] = mdpl

    return entry


def payload_to_fhir_medication_statement(
    payload: MedicationStatementCreateSchema | dict[str, Any],
) -> dict[str, Any]:
    res: dict[str, Any] = {"resourceType": "MedicationStatement"}

    status = _val(payload, "status")
    if status is not None:
        res["status"] = status.value if hasattr(status, "value") else str(status)

    cat = _val(payload, "category")
    if cat:
        category = payload_medication_statement_codeable_concept(cat)
        if category:
            res["category"] = category

    # medication[x] (1..1 choice)
    med_cc_in = _val(payload, "medication_codeable_concept")
    med_ref_in = _val(payload, "medication_reference")
    if med_cc_in:
        med_cc = payload_medication_statement_codeable_concept(med_cc_in)
        if med_cc:
            res["medicationCodeableConcept"] = med_cc
    elif med_ref_in:
        med_ref = _reference_with_identifier_from_payload(med_ref_in)
        if med_ref:
            res["medicationReference"] = med_ref

    # subject (1..1)
    subj_in = _val(payload, "subject")
    if subj_in:
        subj = _reference_with_identifier_from_payload(subj_in)
        if subj:
            res["subject"] = subj

    # context
    ctx_in = _val(payload, "context")
    if ctx_in:
        ctx = _reference_with_identifier_from_payload(ctx_in)
        if ctx:
            res["context"] = ctx

    # effective[x]
    eff_dt = _val(payload, "effective_date_time")
    eff_start = _val(payload, "effective_period_start")
    eff_end = _val(payload, "effective_period_end")
    if eff_dt:
        res["effectiveDateTime"] = eff_dt.isoformat() if hasattr(eff_dt, "isoformat") else str(eff_dt)
    elif eff_start or eff_end:
        res["effectivePeriod"] = {
            k: v
            for k, v in {
                "start": eff_start.isoformat() if hasattr(eff_start, "isoformat") else (str(eff_start) if eff_start else None),
                "end": eff_end.isoformat() if hasattr(eff_end, "isoformat") else (str(eff_end) if eff_end else None),
            }.items()
            if v is not None
        }

    date_asserted = _val(payload, "date_asserted")
    if date_asserted:
        res["dateAsserted"] = date_asserted.isoformat() if hasattr(date_asserted, "isoformat") else str(date_asserted)

    # informationSource
    info_src_in = _val(payload, "information_source")
    if info_src_in:
        info_src = _reference_with_identifier_from_payload(info_src_in)
        if info_src:
            res["informationSource"] = info_src

    # basedOn
    bo_in = _val(payload, "based_on")
    if bo_in:
        bo_list = [_reference_with_identifier_from_payload(b) for b in bo_in]
        bo_list = [b for b in bo_list if b]
        if bo_list:
            res["basedOn"] = bo_list

    # partOf
    po_in = _val(payload, "part_of")
    if po_in:
        po_list = [_reference_with_identifier_from_payload(p) for p in po_in]
        po_list = [p for p in po_list if p]
        if po_list:
            res["partOf"] = po_list

    # statusReason
    sr_in = _val(payload, "status_reason")
    if sr_in:
        sr_list = [payload_medication_statement_status_reason(sr) for sr in sr_in]
        sr_list = [sr for sr in sr_list if sr]
        if sr_list:
            res["statusReason"] = sr_list

    # derivedFrom
    df_in = _val(payload, "derived_from")
    if df_in:
        df_list = [_reference_with_identifier_from_payload(df) for df in df_in]
        df_list = [df for df in df_list if df]
        if df_list:
            res["derivedFrom"] = df_list

    # reasonCode
    rc_in = _val(payload, "reason_code")
    if rc_in:
        rc_list = [payload_medication_statement_reason_code(rc) for rc in rc_in]
        rc_list = [rc for rc in rc_list if rc]
        if rc_list:
            res["reasonCode"] = rc_list

    # reasonReference
    rr_in = _val(payload, "reason_reference")
    if rr_in:
        rr_list = [_reference_with_identifier_from_payload(rr) for rr in rr_in]
        rr_list = [rr for rr in rr_list if rr]
        if rr_list:
            res["reasonReference"] = rr_list

    # note
    n_in = _val(payload, "note")
    if n_in:
        n_list = [payload_medication_statement_note(n) for n in n_in]
        n_list = [n for n in n_list if n]
        if n_list:
            res["note"] = n_list

    # dosage
    d_in = _val(payload, "dosage")
    if d_in:
        d_list = [payload_medication_statement_dosage(d) for d in d_in]
        d_list = [d for d in d_list if d]
        if d_list:
            res["dosage"] = d_list

    # identifier
    id_in = _val(payload, "identifier")
    if id_in:
        id_list = [payload_medication_statement_identifier(i) for i in id_in]
        id_list = [i for i in id_list if i]
        if id_list:
            res["identifier"] = id_list

    ext_in = _val(payload, "extension")
    if ext_in:
        res["extension"] = list(ext_in)

    return {k: v for k, v in res.items() if v is not None}


def patch_fragment_to_fhir_medication_statement(
    payload: MedicationStatementPatchSchema,
) -> tuple[dict[str, Any], set[str]]:
    provided = payload.model_dump(exclude_unset=True)
    fragment: dict[str, Any] = {}
    touched: set[str] = set()

    if "status" in provided:
        touched.add("status")
        if payload.status is not None:
            fragment["status"] = (
                payload.status.value if hasattr(payload.status, "value") else str(payload.status)
            )

    if "category" in provided:
        touched.add("category")
        if payload.category is not None:
            cat = payload_medication_statement_codeable_concept(payload.category)
            if cat:
                fragment["category"] = cat

    if provided.keys() & _MEDICATION_FIELDS:
        touched.update(_MEDICATION_FHIR_KEYS)
        if payload.medication_codeable_concept is not None:
            med_cc = payload_medication_statement_codeable_concept(payload.medication_codeable_concept)
            if med_cc:
                fragment["medicationCodeableConcept"] = med_cc
        elif payload.medication_reference is not None:
            med_ref = _reference_with_identifier_from_payload(payload.medication_reference)
            if med_ref:
                fragment["medicationReference"] = med_ref

    if "subject" in provided:
        touched.add("subject")
        if payload.subject is not None:
            subj = _reference_with_identifier_from_payload(payload.subject)
            if subj:
                fragment["subject"] = subj

    if "context" in provided:
        touched.add("context")
        if payload.context is not None:
            ctx = _reference_with_identifier_from_payload(payload.context)
            if ctx:
                fragment["context"] = ctx

    if provided.keys() & _EFFECTIVE_FIELDS:
        touched.update(_EFFECTIVE_FHIR_KEYS)
        if payload.effective_date_time is not None:
            fragment["effectiveDateTime"] = (
                payload.effective_date_time.isoformat()
                if hasattr(payload.effective_date_time, "isoformat")
                else str(payload.effective_date_time)
            )
        elif payload.effective_period_start is not None or payload.effective_period_end is not None:
            fragment["effectivePeriod"] = {
                k: v
                for k, v in {
                    "start": (
                        payload.effective_period_start.isoformat()
                        if hasattr(payload.effective_period_start, "isoformat")
                        else str(payload.effective_period_start)
                    )
                    if payload.effective_period_start
                    else None,
                    "end": (
                        payload.effective_period_end.isoformat()
                        if hasattr(payload.effective_period_end, "isoformat")
                        else str(payload.effective_period_end)
                    )
                    if payload.effective_period_end
                    else None,
                }.items()
                if v is not None
            }

    if "date_asserted" in provided:
        touched.add("dateAsserted")
        if payload.date_asserted is not None:
            fragment["dateAsserted"] = (
                payload.date_asserted.isoformat()
                if hasattr(payload.date_asserted, "isoformat")
                else str(payload.date_asserted)
            )

    if "information_source" in provided:
        touched.add("informationSource")
        if payload.information_source is not None:
            info_src = _reference_with_identifier_from_payload(payload.information_source)
            if info_src:
                fragment["informationSource"] = info_src

    if "based_on" in provided:
        touched.add("basedOn")
        if payload.based_on is not None:
            bo_list = [_reference_with_identifier_from_payload(b) for b in payload.based_on]
            bo_list = [b for b in bo_list if b]
            if bo_list:
                fragment["basedOn"] = bo_list

    if "part_of" in provided:
        touched.add("partOf")
        if payload.part_of is not None:
            po_list = [_reference_with_identifier_from_payload(p) for p in payload.part_of]
            po_list = [p for p in po_list if p]
            if po_list:
                fragment["partOf"] = po_list

    if "status_reason" in provided:
        touched.add("statusReason")
        if payload.status_reason is not None:
            sr_list = [payload_medication_statement_status_reason(sr) for sr in payload.status_reason]
            sr_list = [sr for sr in sr_list if sr]
            if sr_list:
                fragment["statusReason"] = sr_list

    if "derived_from" in provided:
        touched.add("derivedFrom")
        if payload.derived_from is not None:
            df_list = [_reference_with_identifier_from_payload(df) for df in payload.derived_from]
            df_list = [df for df in df_list if df]
            if df_list:
                fragment["derivedFrom"] = df_list

    if "reason_code" in provided:
        touched.add("reasonCode")
        if payload.reason_code is not None:
            rc_list = [payload_medication_statement_reason_code(rc) for rc in payload.reason_code]
            rc_list = [rc for rc in rc_list if rc]
            if rc_list:
                fragment["reasonCode"] = rc_list

    if "reason_reference" in provided:
        touched.add("reasonReference")
        if payload.reason_reference is not None:
            rr_list = [_reference_with_identifier_from_payload(rr) for rr in payload.reason_reference]
            rr_list = [rr for rr in rr_list if rr]
            if rr_list:
                fragment["reasonReference"] = rr_list

    if "note" in provided:
        touched.add("note")
        if payload.note is not None:
            n_list = [payload_medication_statement_note(n) for n in payload.note]
            n_list = [n for n in n_list if n]
            if n_list:
                fragment["note"] = n_list

    if "dosage" in provided:
        touched.add("dosage")
        if payload.dosage is not None:
            d_list = [payload_medication_statement_dosage(d) for d in payload.dosage]
            d_list = [d for d in d_list if d]
            if d_list:
                fragment["dosage"] = d_list

    if "identifier" in provided:
        touched.add("identifier")
        if payload.identifier is not None:
            id_list = [payload_medication_statement_identifier(i) for i in payload.identifier]
            id_list = [i for i in id_list if i]
            if id_list:
                fragment["identifier"] = id_list

    if "extension" in provided:
        touched.add("extension")
        if payload.extension is not None:
            fragment["extension"] = list(payload.extension)

    return fragment, touched
