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
    assigner = _fhir_reference(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _fhir_annotation(note) -> dict | None:
    entry: dict = {}
    author_ref = _fhir_reference(note, "author_reference")
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
        or act.detail_location_identifier_value
        or getattr(act, "detail_performers", None)
        or act.detail_product_codeable_concept_text
        or getattr(act, "detail_product_codings", None)
        or act.detail_product_reference
        or act.detail_product_type
        or act.detail_product_id
        or act.detail_product_display
        or act.detail_product_identifier_value
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
            _fhir_reference(rr, "reference")
            for rr in act.detail_reason_references
        ]
        rr_list = [rr for rr in rr_list if rr]
        if rr_list:
            detail["reasonReference"] = rr_list
    if getattr(act, "detail_goals", None):
        goal_list = [
            _fhir_reference(g, "reference")
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
    loc = _fhir_reference(act, "detail_location")
    if loc:
        detail["location"] = loc
    if getattr(act, "detail_performers", None):
        perf_list = [
            _fhir_reference(p, "reference")
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
    prod_ref = _fhir_reference(act, "detail_product")
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
            _fhir_reference(oref, "reference")
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
    ref = _fhir_reference(act, "reference")
    if ref:
        res["reference"] = ref
    det = _fhir_activity_detail(act)
    if det:
        res["detail"] = det
    return res


def _fhir_meta(model: CarePlanModel) -> dict:
    meta: dict = {}
    last_updated = model.updated_at or model.created_at
    if last_updated:
        meta["lastUpdated"] = fhir_instant(last_updated)
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
            _fhir_reference(b, "reference")
            for b in model.based_on
        ]
        bo_list = [b for b in bo_list if b]
        if bo_list:
            res["basedOn"] = bo_list

    if getattr(model, "replaces", None):
        rep_list = [
            _fhir_reference(r, "reference")
            for r in model.replaces
        ]
        rep_list = [r for r in rep_list if r]
        if rep_list:
            res["replaces"] = rep_list

    if getattr(model, "part_of", None):
        po_list = [
            _fhir_reference(p, "reference")
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

    subj = _fhir_reference(model, "subject")
    if subj:
        res["subject"] = subj

    enc = _fhir_reference(model, "encounter")
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

    auth = _fhir_reference(model, "author")
    if auth:
        res["author"] = auth

    if getattr(model, "contributors", None):
        cont_list = [
            _fhir_reference(c, "reference")
            for c in model.contributors
        ]
        cont_list = [c for c in cont_list if c]
        if cont_list:
            res["contributor"] = cont_list

    if getattr(model, "care_teams", None):
        ct_list = [
            _fhir_reference(ct, "reference")
            for ct in model.care_teams
        ]
        ct_list = [ct for ct in ct_list if ct]
        if ct_list:
            res["careTeam"] = ct_list

    if getattr(model, "addresses", None):
        addr_list = [
            _fhir_reference(a, "reference")
            for a in model.addresses
        ]
        addr_list = [a for a in addr_list if a]
        if addr_list:
            res["addresses"] = addr_list

    if getattr(model, "goals", None):
        goal_list = [
            _fhir_reference(g, "reference")
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
