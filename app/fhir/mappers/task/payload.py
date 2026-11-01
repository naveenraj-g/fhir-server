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

_IDENTIFIER_SUFFIXES = {
    "identifier_use",
    "identifier_type_system",
    "identifier_type_version",
    "identifier_type_code",
    "identifier_type_display",
    "identifier_type_text",
    "identifier_type_user_selected",
    "identifier_system",
    "identifier_value",
    "identifier_period_start",
    "identifier_period_end",
}

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
} | {f"group_identifier_assigner_{s}" for s in _IDENTIFIER_SUFFIXES}
_FOCUS_FIELDS = {"focus", "focus_display"} | {f"focus_{s}" for s in _IDENTIFIER_SUFFIXES}
_FOR_FIELDS = {"for_", "for", "for_display"} | {f"for_{s}" for s in _IDENTIFIER_SUFFIXES}
_ENCOUNTER_FIELDS = {"encounter", "encounter_display"} | {f"encounter_{s}" for s in _IDENTIFIER_SUFFIXES}
_EXECUTION_PERIOD_FIELDS = {"execution_period_start", "execution_period_end"}
_REQUESTER_FIELDS = {"requester", "requester_display"} | {f"requester_{s}" for s in _IDENTIFIER_SUFFIXES}
_OWNER_FIELDS = {"owner", "owner_display"} | {f"owner_{s}" for s in _IDENTIFIER_SUFFIXES}
_LOCATION_FIELDS = {"location", "location_display"} | {f"location_{s}" for s in _IDENTIFIER_SUFFIXES}
_REASON_REF_FIELDS = {"reason_reference", "reason_reference_display"} | {f"reason_reference_{s}" for s in _IDENTIFIER_SUFFIXES}


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


def _reference_from_payload(obj: Any, prefix: str) -> dict | None:
    def _get(field):
        return obj.get(field) if isinstance(obj, dict) else getattr(obj, field, None)

    raw_reference = _get(prefix)
    if prefix == "for" and raw_reference is None:
        raw_reference = _get("for_")
    display = _get(f"{prefix}_display")

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    if display:
        entry["display"] = display

    id_use = _get(f"{prefix}_identifier_use")
    id_type_system = _get(f"{prefix}_identifier_type_system")
    id_type_version = _get(f"{prefix}_identifier_type_version")
    id_type_code = _get(f"{prefix}_identifier_type_code")
    id_type_display = _get(f"{prefix}_identifier_type_display")
    id_type_text = _get(f"{prefix}_identifier_type_text")
    id_type_user_selected = _get(f"{prefix}_identifier_type_user_selected")
    id_system = _get(f"{prefix}_identifier_system")
    id_value = _get(f"{prefix}_identifier_value")
    id_period_start = _get(f"{prefix}_identifier_period_start")
    id_period_end = _get(f"{prefix}_identifier_period_end")

    if id_use or id_type_system or id_type_code or id_type_text or id_system or id_value:
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
        if id_type_system or id_type_code or id_type_text:
            type_cc: dict = {}
            if id_type_system or id_type_code:
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
                    "start": fhir_instant(id_period_start),
                    "end": fhir_instant(id_period_end),
                }.items()
                if v
            }
        entry["identifier"] = identifier
    return entry or None


def _ref_from_payload(ref: Any, display: str | None = None) -> dict | None:
    if not ref and not display:
        return None
    if isinstance(ref, str):
        result = {"reference": ref}
        if display:
            result["display"] = display
        return result

    result = {}
    r = getattr(ref, "reference", None) if not isinstance(ref, dict) else ref.get("reference")
    if r:
        result["reference"] = r
    d = (getattr(ref, "display", None) if not isinstance(ref, dict) else ref.get("display")) or display
    if d:
        result["display"] = d

    def _get(field):
        return ref.get(field) if isinstance(ref, dict) else getattr(ref, field, None)

    id_use = _get("identifier_use")
    id_type_system = _get("identifier_type_system")
    id_type_version = _get("identifier_type_version")
    id_type_code = _get("identifier_type_code")
    id_type_display = _get("identifier_type_display")
    id_type_text = _get("identifier_type_text")
    id_type_user_selected = _get("identifier_type_user_selected")
    id_system = _get("identifier_system")
    id_value = _get("identifier_value")
    id_period_start = _get("identifier_period_start")
    id_period_end = _get("identifier_period_end")

    if id_use or id_type_system or id_type_code or id_type_text or id_system or id_value:
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
        if id_type_system or id_type_code or id_type_text:
            type_cc: dict = {}
            if id_type_system or id_type_code:
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
                    "start": fhir_instant(id_period_start),
                    "end": fhir_instant(id_period_end),
                }.items()
                if v
            }
        result["identifier"] = identifier

    return result or None


def _identifier_from_payload(i: TaskIdentifierInput | dict) -> dict | None:
    if not i:
        return None
    entry: dict = {}
    use = getattr(i, "use", None) or (i.get("use") if isinstance(i, dict) else None)
    if use:
        entry["use"] = fhir_enum(use)
    type_codings = [
        _coding_from_payload(c)
        for c in (
            (i.get("type_coding") if isinstance(i, dict) else i.type_coding) or []
        )
    ]
    type_cc: dict = {}
    if type_codings:
        type_cc["coding"] = type_codings
    type_text = getattr(i, "type_text", None) or (
        i.get("type_text") if isinstance(i, dict) else None
    )
    if type_text:
        type_cc["text"] = type_text
    if type_cc:
        entry["type"] = type_cc
    system = getattr(i, "system", None) or (
        i.get("system") if isinstance(i, dict) else None
    )
    if system:
        entry["system"] = system
    value = getattr(i, "value", None) or (
        i.get("value") if isinstance(i, dict) else None
    )
    if value:
        entry["value"] = value
    p_start = getattr(i, "period_start", None) or (
        i.get("period_start") if isinstance(i, dict) else None
    )
    p_end = getattr(i, "period_end", None) or (
        i.get("period_end") if isinstance(i, dict) else None
    )
    if p_start or p_end:
        period: dict = {}
        if p_start:
            period["start"] = fhir_instant(p_start)
        if p_end:
            period["end"] = fhir_instant(p_end)
        entry["period"] = period
    assigner = _reference_from_payload(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _group_identifier_from_payload(payload: Any) -> dict | None:
    entry: dict = {}
    use = getattr(payload, "group_identifier_use", None) or (
        payload.get("group_identifier_use") if isinstance(payload, dict) else None
    )
    if use:
        entry["use"] = fhir_enum(use)
    system = getattr(payload, "group_identifier_system", None) or (
        payload.get("group_identifier_system") if isinstance(payload, dict) else None
    )
    if system:
        entry["system"] = system
    value = getattr(payload, "group_identifier_value", None) or (
        payload.get("group_identifier_value") if isinstance(payload, dict) else None
    )
    if value:
        entry["value"] = value
    p_start = getattr(payload, "group_identifier_period_start", None) or (
        payload.get("group_identifier_period_start") if isinstance(payload, dict) else None
    )
    p_end = getattr(payload, "group_identifier_period_end", None) or (
        payload.get("group_identifier_period_end") if isinstance(payload, dict) else None
    )
    if p_start or p_end:
        period = {}
        if p_start:
            period["start"] = fhir_instant(p_start)
        if p_end:
            period["end"] = fhir_instant(p_end)
        entry["period"] = period
    assigner = _reference_from_payload(payload, "group_identifier_assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _performer_type_from_payload(pt: TaskPerformerTypeInput | dict) -> dict | None:
    if isinstance(pt, dict):
        return _codeable_concept_from_payload(pt.get("coding"), pt.get("text"))
    return _codeable_concept_from_payload(pt.coding, pt.text)


def _note_from_payload(n: TaskNoteInput | dict) -> dict | None:
    if not n:
        return None
    entry: dict = {}
    auth_str = getattr(n, "author_string", None) or (
        n.get("author_string") if isinstance(n, dict) else None
    )
    if auth_str:
        entry["authorString"] = auth_str
    else:
        author_ref = _reference_from_payload(n, "author")
        if author_ref:
            entry["authorReference"] = author_ref
    time = getattr(n, "time", None) or (
        n.get("time") if isinstance(n, dict) else None
    )
    if time:
        entry["time"] = fhir_instant(time)
    text = getattr(n, "text", None) or (
        n.get("text") if isinstance(n, dict) else None
    )
    if text:
        entry["text"] = text
    return entry or None


def _restriction_from_payload(r: TaskRestrictionInput | dict) -> dict | None:
    if not r:
        return None
    def _get(field):
        return r.get(field) if isinstance(r, dict) else getattr(r, field, None)

    res: dict = {}
    reps = _get("repetitions")
    if reps is not None:
        res["repetitions"] = reps
    p_start = _get("period_start")
    p_end = _get("period_end")
    if p_start or p_end:
        p: dict = {}
        if p_start:
            p["start"] = fhir_instant(p_start)
        if p_end:
            p["end"] = fhir_instant(p_end)
        res["period"] = p
    recip_list = _get("recipient")
    if recip_list:
        recips = [_ref_from_payload(rec) for rec in recip_list]
        res["recipient"] = [x for x in recips if x is not None]
    return res or None


def _input_from_payload(inp: TaskInputInput | dict) -> dict | None:
    if not inp:
        return None
    def _get(field):
        return inp.get(field) if isinstance(inp, dict) else getattr(inp, field, None)

    type_codings = _get("type_coding")
    type_text = _get("type_text")
    type_cc = _codeable_concept_from_payload(type_codings, type_text)
    if not type_cc:
        return None
    res: dict = {"type": type_cc}

    for k_in, k_fhir, is_dt, is_flt, is_date, is_time in [
        ("value_string", "valueString", False, False, False, False),
        ("value_boolean", "valueBoolean", False, False, False, False),
        ("value_integer", "valueInteger", False, False, False, False),
        ("value_decimal", "valueDecimal", False, True, False, False),
        ("value_date", "valueDate", False, False, True, False),
        ("value_date_time", "valueDateTime", True, False, False, False),
        ("value_time", "valueTime", False, False, False, True),
        ("value_uri", "valueUri", False, False, False, False),
        ("value_code", "valueCode", False, False, False, False),
    ]:
        v = _get(k_in)
        if v is not None:
            if is_flt:
                res[k_fhir] = float(v)
            elif is_date:
                res[k_fhir] = _format_date(v)
            elif is_dt:
                res[k_fhir] = fhir_instant(v)
            elif is_time:
                res[k_fhir] = str(v)
            else:
                res[k_fhir] = v
            break
    else:
        val_ref = _reference_from_payload(inp, "value_reference")
        if val_ref:
            res["valueReference"] = val_ref
        else:
            val_json = _get("value_json")
            if val_json is not None and isinstance(val_json, dict):
                res.update(val_json)
    return res


def _output_from_payload(out: TaskOutputInput | dict) -> dict | None:
    if not out:
        return None
    def _get(field):
        return out.get(field) if isinstance(out, dict) else getattr(out, field, None)

    type_codings = _get("type_coding")
    type_text = _get("type_text")
    type_cc = _codeable_concept_from_payload(type_codings, type_text)
    if not type_cc:
        return None
    res: dict = {"type": type_cc}

    for k_in, k_fhir, is_dt, is_flt, is_date, is_time in [
        ("value_string", "valueString", False, False, False, False),
        ("value_boolean", "valueBoolean", False, False, False, False),
        ("value_integer", "valueInteger", False, False, False, False),
        ("value_decimal", "valueDecimal", False, True, False, False),
        ("value_date", "valueDate", False, False, True, False),
        ("value_date_time", "valueDateTime", True, False, False, False),
        ("value_time", "valueTime", False, False, False, True),
        ("value_uri", "valueUri", False, False, False, False),
        ("value_code", "valueCode", False, False, False, False),
    ]:
        v = _get(k_in)
        if v is not None:
            if is_flt:
                res[k_fhir] = float(v)
            elif is_date:
                res[k_fhir] = _format_date(v)
            elif is_dt:
                res[k_fhir] = fhir_instant(v)
            elif is_time:
                res[k_fhir] = str(v)
            else:
                res[k_fhir] = v
            break
    else:
        val_ref = _reference_from_payload(out, "value_reference")
        if val_ref:
            res["valueReference"] = val_ref
        else:
            val_json = _get("value_json")
            if val_json is not None and isinstance(val_json, dict):
                res.update(val_json)
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

    focus = _reference_from_payload(payload, "focus")
    if focus:
        result["focus"] = focus

    for_ref = _reference_from_payload(payload, "for")
    if for_ref:
        result["for"] = for_ref

    encounter = _reference_from_payload(payload, "encounter")
    if encounter:
        result["encounter"] = encounter

    if payload.execution_period_start or payload.execution_period_end:
        period = {}
        if payload.execution_period_start:
            period["start"] = fhir_instant(payload.execution_period_start)
        if payload.execution_period_end:
            period["end"] = fhir_instant(payload.execution_period_end)
        result["executionPeriod"] = period

    requester = _reference_from_payload(payload, "requester")
    if requester:
        result["requester"] = requester

    owner = _reference_from_payload(payload, "owner")
    if owner:
        result["owner"] = owner

    location = _reference_from_payload(payload, "location")
    if location:
        result["location"] = location

    reason_ref = _reference_from_payload(payload, "reason_reference")
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
        focus = _reference_from_payload(payload, "focus")
        if focus:
            fragment["focus"] = focus

    if _FOR_FIELDS & fields_set:
        touched.add("for")
        for_ref = _reference_from_payload(payload, "for")
        if for_ref:
            fragment["for"] = for_ref

    if _ENCOUNTER_FIELDS & fields_set:
        touched.add("encounter")
        encounter = _reference_from_payload(payload, "encounter")
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
        requester = _reference_from_payload(payload, "requester")
        if requester:
            fragment["requester"] = requester

    if _OWNER_FIELDS & fields_set:
        touched.add("owner")
        owner = _reference_from_payload(payload, "owner")
        if owner:
            fragment["owner"] = owner

    if _LOCATION_FIELDS & fields_set:
        touched.add("location")
        location = _reference_from_payload(payload, "location")
        if location:
            fragment["location"] = location

    if _REASON_REF_FIELDS & fields_set:
        touched.add("reasonReference")
        reason_ref = _reference_from_payload(payload, "reason_reference")
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
