from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.care_plan import CarePlanActivity, CarePlanModel


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

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)

    if id_use or id_system or id_value or id_type_text:
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        if id_type_text:
            identifier["type"] = {"text": id_type_text}
        entry["identifier"] = identifier

    return entry or None


def _fhir_identifier(i) -> dict | None:
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
    assigner = _fhir_reference_with_identifier_fallback(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _fhir_annotation(note) -> dict | None:
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


def _fhir_quantity(val, comp, unit, system, code) -> dict | None:
    if val is None and comp is None and unit is None and system is None and code is None:
        return None
    res: dict = {}
    if val is not None:
        res["value"] = float(val)
    if comp is not None:
        res["comparator"] = fhir_enum(comp)
    if unit is not None:
        res["unit"] = unit
    if system is not None:
        res["system"] = system
    if code is not None:
        res["code"] = code
    return res or None


def _fhir_activity_detail(act: CarePlanActivity) -> dict | None:
    has_any = (
        act.detail_kind is not None
        or act.detail_instantiates_canonical
        or act.detail_instantiates_uri
        or act.detail_code_text
        or getattr(act, "detail_code_codings", None)
        or act.detail_status is not None
        or act.detail_status_reason_text
        or getattr(act, "detail_status_reason_codings", None)
        or act.detail_do_not_perform is not None
        or act.detail_scheduled_timing
        or act.detail_scheduled_period_start
        or act.detail_scheduled_period_end
        or act.detail_scheduled_string
        or act.detail_location_reference
        or act.detail_location_type
        or act.detail_location_id
        or act.detail_location_display
        or getattr(act, "detail_performers", None)
        or act.detail_product_codeable_concept_text
        or getattr(act, "detail_product_codings", None)
        or act.detail_product_reference
        or act.detail_product_type
        or act.detail_product_id
        or act.detail_product_display
        or act.detail_daily_amount_value is not None
        or act.detail_quantity_value is not None
        or act.detail_description
        or getattr(act, "detail_reason_codes", None)
        or getattr(act, "detail_reason_references", None)
        or getattr(act, "detail_goals", None)
    )
    if not has_any:
        return None

    detail: dict = {}
    if act.detail_kind:
        detail["kind"] = fhir_enum(act.detail_kind)
    if act.detail_instantiates_canonical:
        detail["instantiatesCanonical"] = list(act.detail_instantiates_canonical)
    if act.detail_instantiates_uri:
        detail["instantiatesUri"] = list(act.detail_instantiates_uri)
    code_cc = _fhir_codeable_concept(getattr(act, "detail_code_codings", None), act.detail_code_text)
    if code_cc:
        detail["code"] = code_cc
    if getattr(act, "detail_reason_codes", None):
        rc_list = [
            _fhir_codeable_concept(getattr(rc, "codings", None), rc.text)
            for rc in act.detail_reason_codes
        ]
        rc_list = [rc for rc in rc_list if rc]
        if rc_list:
            detail["reasonCode"] = rc_list
    if getattr(act, "detail_reason_references", None):
        rr_list = [
            _fhir_ref(rr.reference_reference, rr.reference_type, rr.reference_id, rr.reference_display)
            for rr in act.detail_reason_references
        ]
        rr_list = [rr for rr in rr_list if rr]
        if rr_list:
            detail["reasonReference"] = rr_list
    if getattr(act, "detail_goals", None):
        goal_list = [
            _fhir_ref(g.reference_reference, g.reference_type, g.reference_id, g.reference_display)
            for g in act.detail_goals
        ]
        goal_list = [g for g in goal_list if g]
        if goal_list:
            detail["goal"] = goal_list
    if act.detail_status:
        detail["status"] = fhir_enum(act.detail_status)
    status_reason_cc = _fhir_codeable_concept(
        getattr(act, "detail_status_reason_codings", None),
        act.detail_status_reason_text,
    )
    if status_reason_cc:
        detail["statusReason"] = status_reason_cc
    if act.detail_do_not_perform is not None:
        detail["doNotPerform"] = act.detail_do_not_perform
    if act.detail_scheduled_timing:
        detail["scheduledTiming"] = act.detail_scheduled_timing
    if act.detail_scheduled_period_start or act.detail_scheduled_period_end:
        period: dict = {}
        if act.detail_scheduled_period_start:
            period["start"] = fhir_instant(act.detail_scheduled_period_start)
        if act.detail_scheduled_period_end:
            period["end"] = fhir_instant(act.detail_scheduled_period_end)
        detail["scheduledPeriod"] = period
    if act.detail_scheduled_string:
        detail["scheduledString"] = act.detail_scheduled_string
    loc = _fhir_ref(
        act.detail_location_reference,
        act.detail_location_type,
        act.detail_location_id,
        act.detail_location_display,
    )
    if loc:
        detail["location"] = loc
    if getattr(act, "detail_performers", None):
        perf_list = [
            _fhir_ref(p.reference_reference, p.reference_type, p.reference_id, p.reference_display)
            for p in act.detail_performers
        ]
        perf_list = [p for p in perf_list if p]
        if perf_list:
            detail["performer"] = perf_list
    prod_cc = _fhir_codeable_concept(
        getattr(act, "detail_product_codings", None),
        act.detail_product_codeable_concept_text,
    )
    if prod_cc:
        detail["productCodeableConcept"] = prod_cc
    prod_ref = _fhir_ref(
        act.detail_product_reference,
        act.detail_product_type,
        act.detail_product_id,
        act.detail_product_display,
    )
    if prod_ref:
        detail["productReference"] = prod_ref
    daily_amount = _fhir_quantity(
        act.detail_daily_amount_value,
        act.detail_daily_amount_comparator,
        act.detail_daily_amount_unit,
        act.detail_daily_amount_system,
        act.detail_daily_amount_code,
    )
    if daily_amount:
        detail["dailyAmount"] = daily_amount
    qty = _fhir_quantity(
        act.detail_quantity_value,
        act.detail_quantity_comparator,
        act.detail_quantity_unit,
        act.detail_quantity_system,
        act.detail_quantity_code,
    )
    if qty:
        detail["quantity"] = qty
    if act.detail_description:
        detail["description"] = act.detail_description

    return detail or None


def _fhir_activity(act: CarePlanActivity) -> dict:
    res: dict = {}
    if getattr(act, "outcome_codeable_concepts", None):
        occ_list = [
            _fhir_codeable_concept(getattr(occ, "codings", None), occ.text)
            for occ in act.outcome_codeable_concepts
        ]
        occ_list = [o for o in occ_list if o]
        if occ_list:
            res["outcomeCodeableConcept"] = occ_list
    if getattr(act, "outcome_references", None):
        oref_list = [
            _fhir_ref(oref.reference_reference, oref.reference_type, oref.reference_id, oref.reference_display)
            for oref in act.outcome_references
        ]
        oref_list = [o for o in oref_list if o]
        if oref_list:
            res["outcomeReference"] = oref_list
    if getattr(act, "progress", None):
        prog_list = [_fhir_annotation(p) for p in act.progress]
        prog_list = [p for p in prog_list if p]
        if prog_list:
            res["progress"] = prog_list
    ref = _fhir_ref(
        act.reference_reference,
        act.reference_type,
        act.reference_id,
        act.reference_display,
    )
    if ref:
        res["reference"] = ref
    det = _fhir_activity_detail(act)
    if det:
        res["detail"] = det
    return res


def _fhir_meta(model: CarePlanModel) -> dict:
    meta: dict = {}
    if model.updated_at:
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    extensions = []
    if model.created_at:
        extensions.append({
            "url": "http://hl7.org/fhir/StructureDefinition/resource-created",
            "valueDateTime": fhir_instant(model.created_at),
        })
    if model.created_by:
        extensions.append({
            "url": "http://hl7.org/fhir/StructureDefinition/resource-createdBy",
            "valueString": model.created_by,
        })
    if model.updated_by:
        extensions.append({
            "url": "http://hl7.org/fhir/StructureDefinition/resource-updatedBy",
            "valueString": model.updated_by,
        })
    if extensions:
        meta["extension"] = extensions
    return meta


def to_fhir_care_plan(model: CarePlanModel) -> dict:
    """Transform CarePlanModel into FHIR R4 JSON representation."""
    res: dict[str, Any] = {
        "resourceType": "CarePlan",
        "id": str(model.care_plan_id),
    }

    meta = _fhir_meta(model)
    if meta:
        res["meta"] = meta

    if model.extension:
        res["extension"] = model.extension

    if getattr(model, "identifiers", None):
        id_list = [_fhir_identifier(i) for i in model.identifiers]
        id_list = [i for i in id_list if i]
        if id_list:
            res["identifier"] = id_list

    if model.instantiates_canonical:
        res["instantiatesCanonical"] = list(model.instantiates_canonical)

    if model.instantiates_uri:
        res["instantiatesUri"] = list(model.instantiates_uri)

    if getattr(model, "based_on", None):
        bo_list = [
            _fhir_ref(b.reference_reference, b.reference_type, b.reference_id, b.reference_display)
            for b in model.based_on
        ]
        bo_list = [b for b in bo_list if b]
        if bo_list:
            res["basedOn"] = bo_list

    if getattr(model, "replaces", None):
        rep_list = [
            _fhir_ref(r.reference_reference, r.reference_type, r.reference_id, r.reference_display)
            for r in model.replaces
        ]
        rep_list = [r for r in rep_list if r]
        if rep_list:
            res["replaces"] = rep_list

    if getattr(model, "part_of", None):
        po_list = [
            _fhir_ref(p.reference_reference, p.reference_type, p.reference_id, p.reference_display)
            for p in model.part_of
        ]
        po_list = [p for p in po_list if p]
        if po_list:
            res["partOf"] = po_list

    res["status"] = fhir_enum(model.status)
    res["intent"] = fhir_enum(model.intent)

    if getattr(model, "categories", None):
        cat_list = [
            _fhir_codeable_concept(getattr(c, "codings", None), c.text)
            for c in model.categories
        ]
        cat_list = [c for c in cat_list if c]
        if cat_list:
            res["category"] = cat_list

    if model.title:
        res["title"] = model.title

    if model.description:
        res["description"] = model.description

    subj = _fhir_ref(
        model.subject_reference,
        model.subject_type,
        model.subject_id,
        model.subject_display,
    )
    if subj:
        res["subject"] = subj

    enc = _fhir_ref(
        model.encounter_reference,
        model.encounter_type,
        model.encounter_id,
        model.encounter_display,
    )
    if enc:
        res["encounter"] = enc

    if model.period_start or model.period_end:
        period: dict = {}
        if model.period_start:
            period["start"] = fhir_instant(model.period_start)
        if model.period_end:
            period["end"] = fhir_instant(model.period_end)
        res["period"] = period

    if model.created:
        res["created"] = fhir_instant(model.created)

    auth = _fhir_ref(
        model.author_reference,
        model.author_type,
        model.author_id,
        model.author_display,
    )
    if auth:
        res["author"] = auth

    if getattr(model, "contributors", None):
        cont_list = [
            _fhir_ref(c.reference_reference, c.reference_type, c.reference_id, c.reference_display)
            for c in model.contributors
        ]
        cont_list = [c for c in cont_list if c]
        if cont_list:
            res["contributor"] = cont_list

    if getattr(model, "care_teams", None):
        ct_list = [
            _fhir_ref(ct.reference_reference, ct.reference_type, ct.reference_id, ct.reference_display)
            for ct in model.care_teams
        ]
        ct_list = [ct for ct in ct_list if ct]
        if ct_list:
            res["careTeam"] = ct_list

    if getattr(model, "addresses", None):
        addr_list = [
            _fhir_ref(a.reference_reference, a.reference_type, a.reference_id, a.reference_display)
            for a in model.addresses
        ]
        addr_list = [a for a in addr_list if a]
        if addr_list:
            res["addresses"] = addr_list

    if getattr(model, "goals", None):
        goal_list = [
            _fhir_ref(g.reference_reference, g.reference_type, g.reference_id, g.reference_display)
            for g in model.goals
        ]
        goal_list = [g for g in goal_list if g]
        if goal_list:
            res["goal"] = goal_list

    if getattr(model, "activities", None):
        act_list = [_fhir_activity(a) for a in model.activities]
        act_list = [a for a in act_list if a]
        if act_list:
            res["activity"] = act_list

    if getattr(model, "notes", None):
        note_list = [_fhir_annotation(n) for n in model.notes]
        note_list = [n for n in note_list if n]
        if note_list:
            res["note"] = note_list

    return {k: v for k, v in res.items() if v is not None}
