"""Payload -> FHIR JSON conversion for CarePlan.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(CarePlanCreateSchema / CarePlanPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.schemas.care_plan.input import (
        CarePlanActivityDetailInput,
        CarePlanActivityInput,
        CarePlanCodeableConceptInput,
        CarePlanCreateSchema,
        CarePlanIdentifierInput,
        CarePlanNoteInput,
        CarePlanPatchSchema,
        CarePlanQuantityInput,
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


def _codeable_concept_from_payload(concept: CarePlanCodeableConceptInput | None) -> dict | None:
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


def _identifier_from_payload(ident: CarePlanIdentifierInput | None) -> dict | None:
    if not ident:
        return None
    entry: dict = {}
    if ident.use:
        entry["use"] = fhir_enum(ident.use)
    if ident.type:
        type_cc = _codeable_concept_from_payload(ident.type)
        if type_cc:
            entry["type"] = type_cc
    if ident.system:
        entry["system"] = ident.system
    if ident.value:
        entry["value"] = ident.value
    if ident.period_start or ident.period_end:
        period: dict = {}
        if ident.period_start:
            period["start"] = ident.period_start.isoformat()
        if ident.period_end:
            period["end"] = ident.period_end.isoformat()
        entry["period"] = period
    if ident.assigner or ident.assigner_display:
        assigner: dict = {}
        if ident.assigner:
            assigner["reference"] = ident.assigner
        if ident.assigner_display:
            assigner["display"] = ident.assigner_display
        entry["assigner"] = assigner
    return entry or None


def _annotation_from_payload(note: CarePlanNoteInput | None) -> dict | None:
    if not note:
        return None
    entry: dict = {}
    if note.author_reference or note.author_reference_display:
        ref: dict = {}
        if note.author_reference:
            ref["reference"] = note.author_reference
        if note.author_reference_display:
            ref["display"] = note.author_reference_display
        entry["authorReference"] = ref
    elif note.author_string:
        entry["authorString"] = note.author_string
    if note.time:
        entry["time"] = note.time.isoformat()
    if note.text:
        entry["text"] = note.text
    return entry or None


def _quantity_from_payload(qty: CarePlanQuantityInput | None) -> dict | None:
    if not qty:
        return None
    res: dict = {}
    if qty.value is not None:
        res["value"] = float(qty.value)
    if qty.comparator is not None:
        res["comparator"] = fhir_enum(qty.comparator)
    if qty.unit is not None:
        res["unit"] = qty.unit
    if qty.system is not None:
        res["system"] = qty.system
    if qty.code is not None:
        res["code"] = qty.code
    return res or None


def _activity_detail_from_payload(detail: CarePlanActivityDetailInput | None) -> dict | None:
    if not detail:
        return None
    res: dict = {}
    if detail.kind:
        res["kind"] = fhir_enum(detail.kind)
    if detail.instantiates_canonical:
        res["instantiatesCanonical"] = list(detail.instantiates_canonical)
    if detail.instantiates_uri:
        res["instantiatesUri"] = list(detail.instantiates_uri)
    if detail.code:
        c = _codeable_concept_from_payload(detail.code)
        if c:
            res["code"] = c
    if detail.reason_code:
        rc_list = [_codeable_concept_from_payload(rc) for rc in detail.reason_code]
        rc_list = [rc for rc in rc_list if rc]
        if rc_list:
            res["reasonCode"] = rc_list
    if detail.reason_reference:
        rr_list = [{"reference": r} for r in detail.reason_reference if r]
        if rr_list:
            res["reasonReference"] = rr_list
    if detail.goal:
        g_list = [{"reference": g} for g in detail.goal if g]
        if g_list:
            res["goal"] = g_list
    if detail.status:
        res["status"] = fhir_enum(detail.status)
    if detail.status_reason:
        sr = _codeable_concept_from_payload(detail.status_reason)
        if sr:
            res["statusReason"] = sr
    if detail.do_not_perform is not None:
        res["doNotPerform"] = detail.do_not_perform
    if detail.scheduled_timing:
        res["scheduledTiming"] = detail.scheduled_timing
    if detail.scheduled_period_start or detail.scheduled_period_end:
        p: dict = {}
        if detail.scheduled_period_start:
            p["start"] = detail.scheduled_period_start.isoformat()
        if detail.scheduled_period_end:
            p["end"] = detail.scheduled_period_end.isoformat()
        res["scheduledPeriod"] = p
    if detail.scheduled_string:
        res["scheduledString"] = detail.scheduled_string
    if detail.location or detail.location_display:
        loc: dict = {}
        if detail.location:
            loc["reference"] = detail.location
        if detail.location_display:
            loc["display"] = detail.location_display
        res["location"] = loc
    if detail.performer:
        perf = [{"reference": p} for p in detail.performer if p]
        if perf:
            res["performer"] = perf
    if detail.product_codeable_concept:
        pcc = _codeable_concept_from_payload(detail.product_codeable_concept)
        if pcc:
            res["productCodeableConcept"] = pcc
    if detail.product_reference or detail.product_display:
        pref: dict = {}
        if detail.product_reference:
            pref["reference"] = detail.product_reference
        if detail.product_display:
            pref["display"] = detail.product_display
        res["productReference"] = pref
    if detail.daily_amount:
        da = _quantity_from_payload(detail.daily_amount)
        if da:
            res["dailyAmount"] = da
    if detail.quantity:
        q = _quantity_from_payload(detail.quantity)
        if q:
            res["quantity"] = q
    if detail.description:
        res["description"] = detail.description
    return res or None


def _activity_from_payload(act: CarePlanActivityInput | None) -> dict | None:
    if not act:
        return None
    res: dict = {}
    if act.outcome_codeable_concept:
        occ_list = [_codeable_concept_from_payload(o) for o in act.outcome_codeable_concept]
        occ_list = [o for o in occ_list if o]
        if occ_list:
            res["outcomeCodeableConcept"] = occ_list
    if act.outcome_reference:
        oref_list = [{"reference": r} for r in act.outcome_reference if r]
        if oref_list:
            res["outcomeReference"] = oref_list
    if act.progress:
        prog_list = [_annotation_from_payload(p) for p in act.progress]
        prog_list = [p for p in prog_list if p]
        if prog_list:
            res["progress"] = prog_list
    if act.reference or act.reference_display:
        ref: dict = {}
        if act.reference:
            ref["reference"] = act.reference
        if act.reference_display:
            ref["display"] = act.reference_display
        res["reference"] = ref
    if act.detail:
        det = _activity_detail_from_payload(act.detail)
        if det:
            res["detail"] = det
    return res or None


def payload_to_fhir_care_plan(payload: CarePlanCreateSchema) -> dict[str, Any]:
    """Convert CarePlanCreateSchema to FHIR R4 JSON representation for validation."""
    res: dict[str, Any] = {
        "resourceType": "CarePlan",
        "status": fhir_enum(payload.status),
        "intent": fhir_enum(payload.intent),
    }

    if payload.instantiates_canonical:
        res["instantiatesCanonical"] = list(payload.instantiates_canonical)

    if payload.instantiates_uri:
        res["instantiatesUri"] = list(payload.instantiates_uri)

    if payload.based_on:
        res["basedOn"] = [{"reference": r} for r in payload.based_on if r]

    if payload.replaces:
        res["replaces"] = [{"reference": r} for r in payload.replaces if r]

    if payload.part_of:
        res["partOf"] = [{"reference": r} for r in payload.part_of if r]

    if payload.category:
        cat_list = [_codeable_concept_from_payload(c) for c in payload.category]
        cat_list = [c for c in cat_list if c]
        if cat_list:
            res["category"] = cat_list

    if payload.title:
        res["title"] = payload.title

    if payload.description:
        res["description"] = payload.description

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

    if payload.period_start or payload.period_end:
        p: dict = {}
        if payload.period_start:
            p["start"] = payload.period_start.isoformat()
        if payload.period_end:
            p["end"] = payload.period_end.isoformat()
        res["period"] = p

    if payload.created:
        res["created"] = payload.created.isoformat()

    if payload.author or payload.author_display:
        auth: dict = {}
        if payload.author:
            auth["reference"] = payload.author
        if payload.author_display:
            auth["display"] = payload.author_display
        res["author"] = auth

    if payload.contributor:
        res["contributor"] = [{"reference": c} for c in payload.contributor if c]

    if payload.care_team:
        res["careTeam"] = [{"reference": ct} for ct in payload.care_team if ct]

    if payload.addresses:
        res["addresses"] = [{"reference": a} for a in payload.addresses if a]

    if payload.goal:
        res["goal"] = [{"reference": g} for g in payload.goal if g]

    if payload.activity:
        act_list = [_activity_from_payload(a) for a in payload.activity]
        act_list = [a for a in act_list if a]
        if act_list:
            res["activity"] = act_list

    if payload.note:
        note_list = [_annotation_from_payload(n) for n in payload.note]
        note_list = [n for n in note_list if n]
        if note_list:
            res["note"] = note_list

    if payload.identifier:
        id_list = [_identifier_from_payload(i) for i in payload.identifier]
        id_list = [i for i in id_list if i]
        if id_list:
            res["identifier"] = id_list

    return {k: v for k, v in res.items() if v is not None}


def patch_fragment_to_fhir_care_plan(
    payload: CarePlanPatchSchema,
) -> tuple[dict, set[str]]:
    """Map touched fields of CarePlanPatchSchema to a partial FHIR dict and set of touched keys."""
    touched: set[str] = set()
    fragment: dict = {}
    fields_set = payload.model_fields_set

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

    if "replaces" in fields_set:
        touched.add("replaces")
        if payload.replaces is not None:
            fragment["replaces"] = [{"reference": r} for r in payload.replaces if r]

    if "part_of" in fields_set:
        touched.add("partOf")
        if payload.part_of is not None:
            fragment["partOf"] = [{"reference": r} for r in payload.part_of if r]

    if "status" in fields_set:
        touched.add("status")
        if payload.status is not None:
            fragment["status"] = fhir_enum(payload.status)

    if "intent" in fields_set:
        touched.add("intent")
        if payload.intent is not None:
            fragment["intent"] = fhir_enum(payload.intent)

    if "category" in fields_set:
        touched.add("category")
        if payload.category is not None:
            fragment["category"] = [
                c for c in [_codeable_concept_from_payload(x) for x in payload.category] if c
            ]

    if "title" in fields_set:
        touched.add("title")
        if payload.title is not None:
            fragment["title"] = payload.title

    if "description" in fields_set:
        touched.add("description")
        if payload.description is not None:
            fragment["description"] = payload.description

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

    if "period_start" in fields_set or "period_end" in fields_set:
        touched.add("period")
        p: dict = {}
        if payload.period_start:
            p["start"] = payload.period_start.isoformat()
        if payload.period_end:
            p["end"] = payload.period_end.isoformat()
        if p:
            fragment["period"] = p

    if "created" in fields_set:
        touched.add("created")
        if payload.created is not None:
            fragment["created"] = payload.created.isoformat()

    if "author" in fields_set or "author_display" in fields_set:
        touched.add("author")
        if payload.author is not None or payload.author_display is not None:
            auth: dict = {}
            if payload.author:
                auth["reference"] = payload.author
            if payload.author_display:
                auth["display"] = payload.author_display
            fragment["author"] = auth

    if "contributor" in fields_set:
        touched.add("contributor")
        if payload.contributor is not None:
            fragment["contributor"] = [{"reference": c} for c in payload.contributor if c]

    if "care_team" in fields_set:
        touched.add("careTeam")
        if payload.care_team is not None:
            fragment["careTeam"] = [{"reference": ct} for ct in payload.care_team if ct]

    if "addresses" in fields_set:
        touched.add("addresses")
        if payload.addresses is not None:
            fragment["addresses"] = [{"reference": a} for a in payload.addresses if a]

    if "goal" in fields_set:
        touched.add("goal")
        if payload.goal is not None:
            fragment["goal"] = [{"reference": g} for g in payload.goal if g]

    if "activity" in fields_set:
        touched.add("activity")
        if payload.activity is not None:
            fragment["activity"] = [
                a for a in [_activity_from_payload(x) for x in payload.activity] if a
            ]

    if "note" in fields_set:
        touched.add("note")
        if payload.note is not None:
            fragment["note"] = [
                n for n in [_annotation_from_payload(x) for x in payload.note] if n
            ]

    if "identifier" in fields_set:
        touched.add("identifier")
        if payload.identifier is not None:
            fragment["identifier"] = [
                i for i in [_identifier_from_payload(x) for x in payload.identifier] if i
            ]

    return fragment, touched
