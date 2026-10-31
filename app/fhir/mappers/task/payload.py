"""Payload -> FHIR JSON conversion for Task.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(TaskCreateSchema / TaskPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant


def _format_date(d) -> str | None:
    if not d:
        return None
    return d.isoformat() if hasattr(d, "isoformat") else str(d)

if TYPE_CHECKING:
    from app.schemas.task.input import (
        TaskCreateSchema,
        TaskIdentifierInput,
        TaskInputInput,
        TaskNoteInput,
        TaskOutputInput,
        TaskPatchSchema,
        TaskPerformerTypeInput,
        TaskRestrictionInput,
    )

_CODE_FIELDS = {"code_coding", "code_text"}
_STATUS_REASON_FIELDS = {"status_reason_coding", "status_reason_text"}
_BUSINESS_STATUS_FIELDS = {"business_status_coding", "business_status_text"}
_REASON_CODE_FIELDS = {"reason_code_coding", "reason_code_text"}
_GROUP_IDENTIFIER_FIELDS = {
    "group_identifier_use",
    "group_identifier_system",
    "group_identifier_value",
    "group_identifier_period_start",
    "group_identifier_period_end",
    "group_identifier_assigner",
    "group_identifier_assigner_display",
}
_FOCUS_FIELDS = {"focus", "focus_display"}
_FOR_FIELDS = {"for_", "for", "for_display"}
_ENCOUNTER_FIELDS = {"encounter", "encounter_display"}
_EXECUTION_PERIOD_FIELDS = {"execution_period_start", "execution_period_end"}
_REQUESTER_FIELDS = {"requester", "requester_display"}
_OWNER_FIELDS = {"owner", "owner_display"}
_LOCATION_FIELDS = {"location", "location_display"}
_REASON_REF_FIELDS = {"reason_reference", "reason_reference_display"}


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
    codings: list | None, text: str | None
) -> dict | None:
    coding_list = [_coding_from_payload(c) for c in (codings or [])]
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _ref_from_payload(ref: Any, display: str | None = None) -> dict | None:
    if not ref and not display:
        return None
    if isinstance(ref, dict):
        result = {}
        if ref.get("reference"):
            result["reference"] = ref["reference"]
        if ref.get("display") or display:
            result["display"] = ref.get("display") or display
        return result or None
    if hasattr(ref, "reference"):
        result = {}
        if getattr(ref, "reference", None):
            result["reference"] = ref.reference
        if getattr(ref, "display", None) or display:
            result["display"] = getattr(ref, "display", None) or display
        return result or None
    result = {}
    if ref:
        result["reference"] = str(ref)
    if display:
        result["display"] = display
    return result or None


def _identifier_from_payload(i: TaskIdentifierInput | dict) -> dict | None:
    if isinstance(i, dict):
        entry: dict = {}
        if i.get("use"):
            entry["use"] = fhir_enum(i["use"])
        type_codings = [
            _coding_from_payload(c) for c in (i.get("type_coding") or [])
        ]
        type_cc: dict = {}
        if type_codings:
            type_cc["coding"] = type_codings
        if i.get("type_text"):
            type_cc["text"] = i["type_text"]
        if type_cc:
            entry["type"] = type_cc
        if i.get("system"):
            entry["system"] = i["system"]
        if i.get("value"):
            entry["value"] = i["value"]
        if i.get("period_start") or i.get("period_end"):
            period: dict = {}
            if i.get("period_start"):
                period["start"] = fhir_instant(i["period_start"])
            if i.get("period_end"):
                period["end"] = fhir_instant(i["period_end"])
            entry["period"] = period
        if i.get("assigner") or i.get("assigner_display"):
            assigner: dict = {}
            if i.get("assigner"):
                assigner["reference"] = i["assigner"]
            if i.get("assigner_display"):
                assigner["display"] = i["assigner_display"]
            entry["assigner"] = assigner
        return entry or None

    entry = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    type_codings = [
        _coding_from_payload(c) for c in (i.type_coding or [])
    ]
    type_cc = {}
    if type_codings:
        type_cc["coding"] = type_codings
    if i.type_text:
        type_cc["text"] = i.type_text
    if type_cc:
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    if i.period_start or i.period_end:
        period = {}
        if i.period_start:
            period["start"] = fhir_instant(i.period_start)
        if i.period_end:
            period["end"] = fhir_instant(i.period_end)
        entry["period"] = period
    if i.assigner or i.assigner_display:
        assigner = {}
        if i.assigner:
            assigner["reference"] = i.assigner
        if i.assigner_display:
            assigner["display"] = i.assigner_display
        entry["assigner"] = assigner
    return entry or None


def _group_identifier_from_payload(payload: Any) -> dict | None:
    entry: dict = {}
    use = getattr(payload, "group_identifier_use", None)
    if use:
        entry["use"] = fhir_enum(use)
    system = getattr(payload, "group_identifier_system", None)
    if system:
        entry["system"] = system
    value = getattr(payload, "group_identifier_value", None)
    if value:
        entry["value"] = value
    p_start = getattr(payload, "group_identifier_period_start", None)
    p_end = getattr(payload, "group_identifier_period_end", None)
    if p_start or p_end:
        period = {}
        if p_start:
            period["start"] = fhir_instant(p_start)
        if p_end:
            period["end"] = fhir_instant(p_end)
        entry["period"] = period
    assigner_ref = getattr(payload, "group_identifier_assigner", None)
    assigner_disp = getattr(payload, "group_identifier_assigner_display", None)
    if assigner_ref or assigner_disp:
        assigner = {}
        if assigner_ref:
            assigner["reference"] = assigner_ref
        if assigner_disp:
            assigner["display"] = assigner_disp
        entry["assigner"] = assigner
    return entry or None


def _performer_type_from_payload(pt: TaskPerformerTypeInput | dict) -> dict | None:
    if isinstance(pt, dict):
        return _codeable_concept_from_payload(pt.get("coding"), pt.get("text"))
    return _codeable_concept_from_payload(pt.coding, pt.text)


def _note_from_payload(n: TaskNoteInput | dict) -> dict | None:
    if isinstance(n, dict):
        entry: dict = {}
        if n.get("author_string"):
            entry["authorString"] = n["author_string"]
        elif n.get("author_reference"):
            author_ref: dict = {"reference": n["author_reference"]}
            if n.get("author_display"):
                author_ref["display"] = n["author_display"]
            entry["authorReference"] = author_ref
        if n.get("time"):
            entry["time"] = fhir_instant(n["time"])
        if n.get("text"):
            entry["text"] = n["text"]
        return entry or None

    entry = {}
    if n.author_string:
        entry["authorString"] = n.author_string
    elif n.author_reference:
        author_ref = {"reference": n.author_reference}
        if n.author_display:
            author_ref["display"] = n.author_display
        entry["authorReference"] = author_ref
    if n.time:
        entry["time"] = fhir_instant(n.time)
    if n.text:
        entry["text"] = n.text
    return entry or None


def _restriction_from_payload(r: TaskRestrictionInput | dict) -> dict | None:
    if isinstance(r, dict):
        res: dict = {}
        if r.get("repetitions") is not None:
            res["repetitions"] = r["repetitions"]
        if r.get("period_start") or r.get("period_end"):
            p: dict = {}
            if r.get("period_start"):
                p["start"] = fhir_instant(r["period_start"])
            if r.get("period_end"):
                p["end"] = fhir_instant(r["period_end"])
            res["period"] = p
        recips = [
            _ref_from_payload(rec) for rec in (r.get("recipient") or [])
        ]
        if recips:
            res["recipient"] = [x for x in recips if x is not None]
        return res or None

    res = {}
    if r.repetitions is not None:
        res["repetitions"] = r.repetitions
    if r.period_start or r.period_end:
        p = {}
        if r.period_start:
            p["start"] = fhir_instant(r.period_start)
        if r.period_end:
            p["end"] = fhir_instant(r.period_end)
        res["period"] = p
    recips = [
        _ref_from_payload(rec) for rec in (r.recipient or [])
    ]
    if recips:
        res["recipient"] = [x for x in recips if x is not None]
    return res or None


def _input_from_payload(inp: TaskInputInput | dict) -> dict | None:
    if isinstance(inp, dict):
        type_cc = _codeable_concept_from_payload(
            inp.get("type_coding"), inp.get("type_text")
        )
        if not type_cc:
            return None
        res: dict = {"type": type_cc}
        if inp.get("value_string") is not None:
            res["valueString"] = inp["value_string"]
        elif inp.get("value_boolean") is not None:
            res["valueBoolean"] = inp["value_boolean"]
        elif inp.get("value_integer") is not None:
            res["valueInteger"] = inp["value_integer"]
        elif inp.get("value_decimal") is not None:
            res["valueDecimal"] = float(inp["value_decimal"])
        elif inp.get("value_date") is not None:
            res["valueDate"] = _format_date(inp["value_date"])
        elif inp.get("value_date_time") is not None:
            res["valueDateTime"] = fhir_instant(inp["value_date_time"])
        elif inp.get("value_time") is not None:
            res["valueTime"] = str(inp["value_time"])
        elif inp.get("value_uri") is not None:
            res["valueUri"] = inp["value_uri"]
        elif inp.get("value_code") is not None:
            res["valueCode"] = inp["value_code"]
        elif inp.get("value_reference"):
            ref = _ref_from_payload(
                inp["value_reference"], inp.get("value_reference_display")
            )
            if ref:
                res["valueReference"] = ref
        elif inp.get("value_json") is not None:
            if isinstance(inp["value_json"], dict):
                res.update(inp["value_json"])
        return res

    type_cc = _codeable_concept_from_payload(inp.type_coding, inp.type_text)
    if not type_cc:
        return None
    res = {"type": type_cc}
    if inp.value_string is not None:
        res["valueString"] = inp.value_string
    elif inp.value_boolean is not None:
        res["valueBoolean"] = inp.value_boolean
    elif inp.value_integer is not None:
        res["valueInteger"] = inp.value_integer
    elif inp.value_decimal is not None:
        res["valueDecimal"] = float(inp.value_decimal)
    elif inp.value_date is not None:
        res["valueDate"] = _format_date(inp.value_date)
    elif inp.value_date_time is not None:
        res["valueDateTime"] = fhir_instant(inp.value_date_time)
    elif inp.value_time is not None:
        res["valueTime"] = str(inp.value_time)
    elif inp.value_uri is not None:
        res["valueUri"] = inp.value_uri
    elif inp.value_code is not None:
        res["valueCode"] = inp.value_code
    elif inp.value_reference:
        ref = _ref_from_payload(inp.value_reference, inp.value_reference_display)
        if ref:
            res["valueReference"] = ref
    elif inp.value_json is not None:
        if isinstance(inp.value_json, dict):
            res.update(inp.value_json)
    return res


def _output_from_payload(out: TaskOutputInput | dict) -> dict | None:
    if isinstance(out, dict):
        type_cc = _codeable_concept_from_payload(
            out.get("type_coding"), out.get("type_text")
        )
        if not type_cc:
            return None
        res: dict = {"type": type_cc}
        if out.get("value_string") is not None:
            res["valueString"] = out["value_string"]
        elif out.get("value_boolean") is not None:
            res["valueBoolean"] = out["value_boolean"]
        elif out.get("value_integer") is not None:
            res["valueInteger"] = out["value_integer"]
        elif out.get("value_decimal") is not None:
            res["valueDecimal"] = float(out["value_decimal"])
        elif out.get("value_date") is not None:
            res["valueDate"] = _format_date(out["value_date"])
        elif out.get("value_date_time") is not None:
            res["valueDateTime"] = fhir_instant(out["value_date_time"])
        elif out.get("value_time") is not None:
            res["valueTime"] = str(out["value_time"])
        elif out.get("value_uri") is not None:
            res["valueUri"] = out["value_uri"]
        elif out.get("value_code") is not None:
            res["valueCode"] = out["value_code"]
        elif out.get("value_reference"):
            ref = _ref_from_payload(
                out["value_reference"], out.get("value_reference_display")
            )
            if ref:
                res["valueReference"] = ref
        elif out.get("value_json") is not None:
            if isinstance(out["value_json"], dict):
                res.update(out["value_json"])
        return res

    type_cc = _codeable_concept_from_payload(out.type_coding, out.type_text)
    if not type_cc:
        return None
    res = {"type": type_cc}
    if out.value_string is not None:
        res["valueString"] = out.value_string
    elif out.value_boolean is not None:
        res["valueBoolean"] = out.value_boolean
    elif out.value_integer is not None:
        res["valueInteger"] = out.value_integer
    elif out.value_decimal is not None:
        res["valueDecimal"] = float(out.value_decimal)
    elif out.value_date is not None:
        res["valueDate"] = _format_date(out.value_date)
    elif out.value_date_time is not None:
        res["valueDateTime"] = fhir_instant(out.value_date_time)
    elif out.value_time is not None:
        res["valueTime"] = str(out.value_time)
    elif out.value_uri is not None:
        res["valueUri"] = out.value_uri
    elif out.value_code is not None:
        res["valueCode"] = out.value_code
    elif out.value_reference:
        ref = _ref_from_payload(out.value_reference, out.value_reference_display)
        if ref:
            res["valueReference"] = ref
    elif out.value_json is not None:
        if isinstance(out.value_json, dict):
            res.update(out.value_json)
    return res


def payload_to_fhir_task(payload: TaskCreateSchema) -> dict:
    """Convert a TaskCreateSchema into a FHIR R4 JSON dict."""
    result: dict[str, Any] = {
        "resourceType": "Task",
        "status": fhir_enum(payload.status),
        "intent": fhir_enum(payload.intent),
    }

    if payload.priority:
        result["priority"] = fhir_enum(payload.priority)

    if payload.description:
        result["description"] = payload.description

    if payload.instantiates_canonical:
        result["instantiatesCanonical"] = payload.instantiates_canonical

    if payload.instantiates_uri:
        result["instantiatesUri"] = payload.instantiates_uri

    if payload.authored_on:
        result["authoredOn"] = fhir_instant(payload.authored_on)

    if payload.last_modified:
        result["lastModified"] = fhir_instant(payload.last_modified)

    code = _codeable_concept_from_payload(payload.code_coding, payload.code_text)
    if code:
        result["code"] = code

    status_reason = _codeable_concept_from_payload(
        payload.status_reason_coding, payload.status_reason_text
    )
    if status_reason:
        result["statusReason"] = status_reason

    business_status = _codeable_concept_from_payload(
        payload.business_status_coding, payload.business_status_text
    )
    if business_status:
        result["businessStatus"] = business_status

    reason_code = _codeable_concept_from_payload(
        payload.reason_code_coding, payload.reason_code_text
    )
    if reason_code:
        result["reasonCode"] = reason_code

    group_id = _group_identifier_from_payload(payload)
    if group_id:
        result["groupIdentifier"] = group_id

    focus = _ref_from_payload(payload.focus, payload.focus_display)
    if focus:
        result["focus"] = focus

    for_val = payload.for_
    for_ref = _ref_from_payload(for_val, payload.for_display)
    if for_ref:
        result["for"] = for_ref

    encounter = _ref_from_payload(payload.encounter, payload.encounter_display)
    if encounter:
        result["encounter"] = encounter

    if payload.execution_period_start or payload.execution_period_end:
        period = {}
        if payload.execution_period_start:
            period["start"] = fhir_instant(payload.execution_period_start)
        if payload.execution_period_end:
            period["end"] = fhir_instant(payload.execution_period_end)
        result["executionPeriod"] = period

    requester = _ref_from_payload(payload.requester, payload.requester_display)
    if requester:
        result["requester"] = requester

    owner = _ref_from_payload(payload.owner, payload.owner_display)
    if owner:
        result["owner"] = owner

    location = _ref_from_payload(payload.location, payload.location_display)
    if location:
        result["location"] = location

    reason_ref = _ref_from_payload(
        payload.reason_reference, payload.reason_reference_display
    )
    if reason_ref:
        result["reasonReference"] = reason_ref

    if payload.identifier:
        identifiers = [
            item
            for item in (_identifier_from_payload(i) for i in payload.identifier)
            if item is not None
        ]
        if identifiers:
            result["identifier"] = identifiers

    if payload.based_on:
        based_on = [
            item
            for item in (_ref_from_payload(r) for r in payload.based_on)
            if item is not None
        ]
        if based_on:
            result["basedOn"] = based_on

    if payload.part_of:
        part_of = [
            item
            for item in (_ref_from_payload(r) for r in payload.part_of)
            if item is not None
        ]
        if part_of:
            result["partOf"] = part_of

    if payload.insurance:
        insurance = [
            item
            for item in (_ref_from_payload(r) for r in payload.insurance)
            if item is not None
        ]
        if insurance:
            result["insurance"] = insurance

    if payload.relevant_history:
        history = [
            item
            for item in (_ref_from_payload(r) for r in payload.relevant_history)
            if item is not None
        ]
        if history:
            result["relevantHistory"] = history

    if payload.performer_type:
        pts = [
            item
            for item in (_performer_type_from_payload(pt) for pt in payload.performer_type)
            if item is not None
        ]
        if pts:
            result["performerType"] = pts

    if payload.note:
        notes = [
            item
            for item in (_note_from_payload(n) for n in payload.note)
            if item is not None
        ]
        if notes:
            result["note"] = notes

    if payload.restriction:
        restriction = _restriction_from_payload(payload.restriction)
        if restriction:
            result["restriction"] = restriction

    if payload.input:
        inputs = [
            item
            for item in (_input_from_payload(inp) for inp in payload.input)
            if item is not None
        ]
        if inputs:
            result["input"] = inputs

    if payload.output:
        outputs = [
            item
            for item in (_output_from_payload(out) for out in payload.output)
            if item is not None
        ]
        if outputs:
            result["output"] = outputs

    return {k: v for k, v in result.items() if v is not None}


def patch_fragment_to_fhir_task(
    payload: TaskPatchSchema,
) -> tuple[dict, set[str]]:
    """Convert a TaskPatchSchema to a partial FHIR dict and set of touched FHIR top-level keys."""
    fragment: dict[str, Any] = {}
    touched: set[str] = set()
    fields_set = payload.model_fields_set

    if "status" in fields_set:
        touched.add("status")
        if payload.status is not None:
            fragment["status"] = fhir_enum(payload.status)

    if "intent" in fields_set:
        touched.add("intent")
        if payload.intent is not None:
            fragment["intent"] = fhir_enum(payload.intent)

    if "priority" in fields_set:
        touched.add("priority")
        if payload.priority is not None:
            fragment["priority"] = fhir_enum(payload.priority)

    if "description" in fields_set:
        touched.add("description")
        if payload.description is not None:
            fragment["description"] = payload.description

    if "instantiates_canonical" in fields_set:
        touched.add("instantiatesCanonical")
        if payload.instantiates_canonical is not None:
            fragment["instantiatesCanonical"] = payload.instantiates_canonical

    if "instantiates_uri" in fields_set:
        touched.add("instantiatesUri")
        if payload.instantiates_uri is not None:
            fragment["instantiatesUri"] = payload.instantiates_uri

    if "authored_on" in fields_set:
        touched.add("authoredOn")
        if payload.authored_on is not None:
            fragment["authoredOn"] = fhir_instant(payload.authored_on)

    if "last_modified" in fields_set:
        touched.add("lastModified")
        if payload.last_modified is not None:
            fragment["lastModified"] = fhir_instant(payload.last_modified)

    if _CODE_FIELDS & fields_set:
        touched.add("code")
        code = _codeable_concept_from_payload(
            payload.code_coding, payload.code_text
        )
        if code:
            fragment["code"] = code

    if _STATUS_REASON_FIELDS & fields_set:
        touched.add("statusReason")
        status_reason = _codeable_concept_from_payload(
            payload.status_reason_coding, payload.status_reason_text
        )
        if status_reason:
            fragment["statusReason"] = status_reason

    if _BUSINESS_STATUS_FIELDS & fields_set:
        touched.add("businessStatus")
        business_status = _codeable_concept_from_payload(
            payload.business_status_coding, payload.business_status_text
        )
        if business_status:
            fragment["businessStatus"] = business_status

    if _REASON_CODE_FIELDS & fields_set:
        touched.add("reasonCode")
        reason_code = _codeable_concept_from_payload(
            payload.reason_code_coding, payload.reason_code_text
        )
        if reason_code:
            fragment["reasonCode"] = reason_code

    if _GROUP_IDENTIFIER_FIELDS & fields_set:
        touched.add("groupIdentifier")
        group_id = _group_identifier_from_payload(payload)
        if group_id:
            fragment["groupIdentifier"] = group_id

    if _FOCUS_FIELDS & fields_set:
        touched.add("focus")
        focus = _ref_from_payload(payload.focus, payload.focus_display)
        if focus:
            fragment["focus"] = focus

    if _FOR_FIELDS & fields_set:
        touched.add("for")
        for_val = payload.for_
        for_ref = _ref_from_payload(for_val, payload.for_display)
        if for_ref:
            fragment["for"] = for_ref

    if _ENCOUNTER_FIELDS & fields_set:
        touched.add("encounter")
        encounter = _ref_from_payload(payload.encounter, payload.encounter_display)
        if encounter:
            fragment["encounter"] = encounter

    if _EXECUTION_PERIOD_FIELDS & fields_set:
        touched.add("executionPeriod")
        period = {}
        if payload.execution_period_start is not None:
            period["start"] = fhir_instant(payload.execution_period_start)
        if payload.execution_period_end is not None:
            period["end"] = fhir_instant(payload.execution_period_end)
        if period:
            fragment["executionPeriod"] = period

    if _REQUESTER_FIELDS & fields_set:
        touched.add("requester")
        requester = _ref_from_payload(payload.requester, payload.requester_display)
        if requester:
            fragment["requester"] = requester

    if _OWNER_FIELDS & fields_set:
        touched.add("owner")
        owner = _ref_from_payload(payload.owner, payload.owner_display)
        if owner:
            fragment["owner"] = owner

    if _LOCATION_FIELDS & fields_set:
        touched.add("location")
        location = _ref_from_payload(payload.location, payload.location_display)
        if location:
            fragment["location"] = location

    if _REASON_REF_FIELDS & fields_set:
        touched.add("reasonReference")
        reason_ref = _ref_from_payload(
            payload.reason_reference, payload.reason_reference_display
        )
        if reason_ref:
            fragment["reasonReference"] = reason_ref

    if "identifier" in fields_set:
        touched.add("identifier")
        if payload.identifier is not None:
            fragment["identifier"] = [
                item
                for item in (_identifier_from_payload(i) for i in payload.identifier)
                if item is not None
            ]

    if "based_on" in fields_set:
        touched.add("basedOn")
        if payload.based_on is not None:
            fragment["basedOn"] = [
                item
                for item in (_ref_from_payload(r) for r in payload.based_on)
                if item is not None
            ]

    if "part_of" in fields_set:
        touched.add("partOf")
        if payload.part_of is not None:
            fragment["partOf"] = [
                item
                for item in (_ref_from_payload(r) for r in payload.part_of)
                if item is not None
            ]

    if "insurance" in fields_set:
        touched.add("insurance")
        if payload.insurance is not None:
            fragment["insurance"] = [
                item
                for item in (_ref_from_payload(r) for r in payload.insurance)
                if item is not None
            ]

    if "relevant_history" in fields_set:
        touched.add("relevantHistory")
        if payload.relevant_history is not None:
            fragment["relevantHistory"] = [
                item
                for item in (_ref_from_payload(r) for r in payload.relevant_history)
                if item is not None
            ]

    if "performer_type" in fields_set:
        touched.add("performerType")
        if payload.performer_type is not None:
            fragment["performerType"] = [
                item
                for item in (
                    _performer_type_from_payload(pt) for pt in payload.performer_type
                )
                if item is not None
            ]

    if "note" in fields_set:
        touched.add("note")
        if payload.note is not None:
            fragment["note"] = [
                item
                for item in (_note_from_payload(n) for n in payload.note)
                if item is not None
            ]

    if "restriction" in fields_set:
        touched.add("restriction")
        if payload.restriction is not None:
            fragment["restriction"] = _restriction_from_payload(payload.restriction)

    if "input" in fields_set:
        touched.add("input")
        if payload.input is not None:
            fragment["input"] = [
                item
                for item in (_input_from_payload(inp) for inp in payload.input)
                if item is not None
            ]

    if "output" in fields_set:
        touched.add("output")
        if payload.output is not None:
            fragment["output"] = [
                item
                for item in (_output_from_payload(out) for out in payload.output)
                if item is not None
            ]

    return fragment, touched
