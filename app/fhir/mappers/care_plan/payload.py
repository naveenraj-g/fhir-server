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


def _reference_from_payload(obj: Any, prefix: str) -> dict | None:
    if obj is None:
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


def _child_reference_from_payload(item: Any) -> dict | None:
    if isinstance(item, str):
        return {"reference": item}
    return _reference_from_payload(item, "reference")


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
    assigner = _reference_from_payload(ident, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _annotation_from_payload(note: CarePlanNoteInput | None) -> dict | None:
    if not note:
        return None
    entry: dict = {}
    author_ref = _reference_from_payload(note, "author_reference")
    if author_ref:
        entry["authorReference"] = author_ref
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
        rr_list = [_child_reference_from_payload(r) for r in detail.reason_reference if r]
        if rr_list:
            res["reasonReference"] = rr_list
    if detail.goal:
        g_list = [_child_reference_from_payload(g) for g in detail.goal if g]
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
    loc = _reference_from_payload(detail, "location")
    if loc:
        res["location"] = loc
    if detail.performer:
        perf = [_child_reference_from_payload(p) for p in detail.performer if p]
        if perf:
            res["performer"] = perf
    if detail.product_codeable_concept:
        pcc = _codeable_concept_from_payload(detail.product_codeable_concept)
        if pcc:
            res["productCodeableConcept"] = pcc
    pref = _reference_from_payload(detail, "product")
    if pref:
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
        oref_list = [_child_reference_from_payload(r) for r in act.outcome_reference if r]
        if oref_list:
            res["outcomeReference"] = oref_list
    if act.progress:
        prog_list = [_annotation_from_payload(p) for p in act.progress]
        prog_list = [p for p in prog_list if p]
        if prog_list:
            res["progress"] = prog_list
    ref = _reference_from_payload(act, "reference")
    if ref:
        res["reference"] = ref
    if act.detail:
        det = _activity_detail_from_payload(act.detail)
        if det:
            res["detail"] = det
    return res or None


_SUBJECT_FIELDS = {
    "subject",
    "subject_display",
    "subject_identifier_use",
    "subject_identifier_type_system",
    "subject_identifier_type_version",
    "subject_identifier_type_code",
    "subject_identifier_type_display",
    "subject_identifier_type_user_selected",
    "subject_identifier_type_text",
    "subject_identifier_system",
    "subject_identifier_value",
    "subject_identifier_period_start",
    "subject_identifier_period_end",
}

_ENCOUNTER_FIELDS = {
    "encounter",
    "encounter_display",
    "encounter_identifier_use",
    "encounter_identifier_type_system",
    "encounter_identifier_type_version",
    "encounter_identifier_type_code",
    "encounter_identifier_type_display",
    "encounter_identifier_type_user_selected",
    "encounter_identifier_type_text",
    "encounter_identifier_system",
    "encounter_identifier_value",
    "encounter_identifier_period_start",
    "encounter_identifier_period_end",
}

_AUTHOR_FIELDS = {
    "author",
    "author_display",
    "author_identifier_use",
    "author_identifier_type_system",
    "author_identifier_type_version",
    "author_identifier_type_code",
    "author_identifier_type_display",
    "author_identifier_type_user_selected",
    "author_identifier_type_text",
    "author_identifier_system",
    "author_identifier_value",
    "author_identifier_period_start",
    "author_identifier_period_end",
}


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
        res["basedOn"] = [_child_reference_from_payload(r) for r in payload.based_on if r]

    if payload.replaces:
        res["replaces"] = [_child_reference_from_payload(r) for r in payload.replaces if r]

    if payload.part_of:
        res["partOf"] = [_child_reference_from_payload(r) for r in payload.part_of if r]

    if payload.category:
        cat_list = [_codeable_concept_from_payload(c) for c in payload.category]
        cat_list = [c for c in cat_list if c]
        if cat_list:
            res["category"] = cat_list

    if payload.title:
        res["title"] = payload.title

    if payload.description:
        res["description"] = payload.description

    subj = _reference_from_payload(payload, "subject")
    if subj:
        res["subject"] = subj

    enc = _reference_from_payload(payload, "encounter")
    if enc:
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

    auth = _reference_from_payload(payload, "author")
    if auth:
        res["author"] = auth

    if payload.contributor:
        res["contributor"] = [_child_reference_from_payload(c) for c in payload.contributor if c]

    if payload.care_team:
        res["careTeam"] = [_child_reference_from_payload(ct) for ct in payload.care_team if ct]

    if payload.addresses:
        res["addresses"] = [_child_reference_from_payload(a) for a in payload.addresses if a]

    if payload.goal:
        res["goal"] = [_child_reference_from_payload(g) for g in payload.goal if g]

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
            fragment["basedOn"] = [_child_reference_from_payload(r) for r in payload.based_on if r]

    if "replaces" in fields_set:
        touched.add("replaces")
        if payload.replaces is not None:
            fragment["replaces"] = [_child_reference_from_payload(r) for r in payload.replaces if r]

    if "part_of" in fields_set:
        touched.add("partOf")
        if payload.part_of is not None:
            fragment["partOf"] = [_child_reference_from_payload(r) for r in payload.part_of if r]

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

    if fields_set & _AUTHOR_FIELDS:
        touched.add("author")
        auth = _reference_from_payload(payload, "author")
        if auth:
            fragment["author"] = auth

    if "contributor" in fields_set:
        touched.add("contributor")
        if payload.contributor is not None:
            fragment["contributor"] = [_child_reference_from_payload(c) for c in payload.contributor if c]

    if "care_team" in fields_set:
        touched.add("careTeam")
        if payload.care_team is not None:
            fragment["careTeam"] = [_child_reference_from_payload(ct) for ct in payload.care_team if ct]

    if "addresses" in fields_set:
        touched.add("addresses")
        if payload.addresses is not None:
            fragment["addresses"] = [_child_reference_from_payload(a) for a in payload.addresses if a]

    if "goal" in fields_set:
        touched.add("goal")
        if payload.goal is not None:
            fragment["goal"] = [_child_reference_from_payload(g) for g in payload.goal if g]

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
