from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant


def _format_date(d) -> str | None:
    if not d:
        return None
    return d.isoformat() if hasattr(d, "isoformat") else str(d)

if TYPE_CHECKING:
    from app.models.task import (
        TaskIdentifier,
        TaskInput,
        TaskModel,
        TaskNote,
        TaskOutput,
        TaskPerformerType,
    )

_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


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


def _fhir_reference(obj, prefix: str) -> dict | None:
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


def _fhir_reference_row(row) -> dict | None:
    return _fhir_reference(row, "reference")


def _fhir_identifier(i: TaskIdentifier) -> dict | None:
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


def _fhir_group_identifier(model: TaskModel) -> dict | None:
    entry: dict = {}
    if model.group_identifier_use:
        entry["use"] = fhir_enum(model.group_identifier_use)
    if model.group_identifier_system:
        entry["system"] = model.group_identifier_system
    if model.group_identifier_value:
        entry["value"] = model.group_identifier_value
    if model.group_identifier_period_start or model.group_identifier_period_end:
        period: dict = {}
        if model.group_identifier_period_start:
            period["start"] = fhir_instant(model.group_identifier_period_start)
        if model.group_identifier_period_end:
            period["end"] = fhir_instant(model.group_identifier_period_end)
        entry["period"] = period
    assigner = _fhir_reference(model, "group_identifier_assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _fhir_performer_type(pt: TaskPerformerType) -> dict | None:
    return _fhir_codeable_concept(getattr(pt, "codings", None), pt.text)


def _fhir_note(n: TaskNote) -> dict | None:
    entry: dict = {}
    if n.author_string:
        entry["authorString"] = n.author_string
    else:
        author_ref = _fhir_reference(n, "author")
        if author_ref:
            entry["authorReference"] = author_ref
    if n.time:
        entry["time"] = fhir_instant(n.time)
    if n.text:
        entry["text"] = n.text
    return entry or None


def _fhir_restriction(model: TaskModel) -> dict | None:
    restriction: dict = {}
    if model.restriction_repetitions is not None:
        restriction["repetitions"] = model.restriction_repetitions
    if model.restriction_period_start or model.restriction_period_end:
        period: dict = {}
        if model.restriction_period_start:
            period["start"] = fhir_instant(model.restriction_period_start)
        if model.restriction_period_end:
            period["end"] = fhir_instant(model.restriction_period_end)
        restriction["period"] = period
    recipients = [
        item
        for item in (_fhir_reference_row(r) for r in (model.restriction_recipients or []))
        if item is not None
    ]
    if recipients:
        restriction["recipient"] = recipients
    return restriction or None


def _fhir_input(inp: TaskInput) -> dict | None:
    type_cc = _fhir_codeable_concept(getattr(inp, "type_codings", None), inp.type_text)
    if not type_cc:
        return None
    entry: dict = {"type": type_cc}
    if inp.value_string is not None:
        entry["valueString"] = inp.value_string
    elif inp.value_boolean is not None:
        entry["valueBoolean"] = inp.value_boolean
    elif inp.value_integer is not None:
        entry["valueInteger"] = inp.value_integer
    elif inp.value_decimal is not None:
        entry["valueDecimal"] = float(inp.value_decimal)
    elif inp.value_date is not None:
        entry["valueDate"] = _format_date(inp.value_date)
    elif inp.value_date_time is not None:
        entry["valueDateTime"] = fhir_instant(inp.value_date_time)
    elif inp.value_time is not None:
        entry["valueTime"] = str(inp.value_time)
    elif inp.value_uri is not None:
        entry["valueUri"] = inp.value_uri
    elif inp.value_code is not None:
        entry["valueCode"] = inp.value_code
    else:
        ref = _fhir_reference(inp, "value_reference")
        if ref:
            entry["valueReference"] = ref
    if inp.value_json is not None:
        if isinstance(inp.value_json, dict):
            entry.update(inp.value_json)
    return entry


def _fhir_output(out: TaskOutput) -> dict | None:
    type_cc = _fhir_codeable_concept(getattr(out, "type_codings", None), out.type_text)
    if not type_cc:
        return None
    entry: dict = {"type": type_cc}
    if out.value_string is not None:
        entry["valueString"] = out.value_string
    elif out.value_boolean is not None:
        entry["valueBoolean"] = out.value_boolean
    elif out.value_integer is not None:
        entry["valueInteger"] = out.value_integer
    elif out.value_decimal is not None:
        entry["valueDecimal"] = float(out.value_decimal)
    elif out.value_date is not None:
        entry["valueDate"] = _format_date(out.value_date)
    elif out.value_date_time is not None:
        entry["valueDateTime"] = fhir_instant(out.value_date_time)
    elif out.value_time is not None:
        entry["valueTime"] = str(out.value_time)
    elif out.value_uri is not None:
        entry["valueUri"] = out.value_uri
    elif out.value_code is not None:
        entry["valueCode"] = out.value_code
    else:
        ref = _fhir_reference(out, "value_reference")
        if ref:
            entry["valueReference"] = ref
    if out.value_json is not None:
        if isinstance(out.value_json, dict):
            entry.update(out.value_json)
    return entry


def _fhir_meta(model: TaskModel) -> dict:
    meta: dict = {}
    if model.updated_at:
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    exts: list[dict] = []
    if model.tenant_id:
        exts.append({"url": f"{_EXT_BASE}/tenant-id", "valueString": model.tenant_id})
    if model.created_by:
        exts.append({"url": f"{_EXT_BASE}/created-by", "valueString": model.created_by})
    if model.updated_by:
        exts.append({"url": f"{_EXT_BASE}/updated-by", "valueString": model.updated_by})
    if exts:
        meta["extension"] = exts
    return meta


def to_fhir_task(model: TaskModel) -> dict:
    """Serialize a TaskModel to full FHIR R4 JSON dict."""
    result: dict[str, Any] = {
        "resourceType": "Task",
        "id": str(model.task_id),
    }

    meta = _fhir_meta(model)
    if meta:
        result["meta"] = meta

    if model.extension:
        result["extension"] = list(model.extension)

    identifiers = [
        item
        for item in (_fhir_identifier(i) for i in (model.identifiers or []))
        if item is not None
    ]
    if identifiers:
        result["identifier"] = identifiers

    if model.instantiates_canonical:
        result["instantiatesCanonical"] = model.instantiates_canonical

    if model.instantiates_uri:
        result["instantiatesUri"] = model.instantiates_uri

    based_on = [
        item
        for item in (_fhir_reference_row(r) for r in (model.based_on_list or []))
        if item is not None
    ]
    if based_on:
        result["basedOn"] = based_on

    group_identifier = _fhir_group_identifier(model)
    if group_identifier:
        result["groupIdentifier"] = group_identifier

    part_of = [
        item
        for item in (_fhir_reference_row(r) for r in (model.part_of_list or []))
        if item is not None
    ]
    if part_of:
        result["partOf"] = part_of

    result["status"] = fhir_enum(model.status)

    status_reason = _fhir_codeable_concept(
        model.status_reason_codings, model.status_reason_text
    )
    if status_reason:
        result["statusReason"] = status_reason

    business_status = _fhir_codeable_concept(
        model.business_status_codings, model.business_status_text
    )
    if business_status:
        result["businessStatus"] = business_status

    result["intent"] = fhir_enum(model.intent)

    if model.priority:
        result["priority"] = fhir_enum(model.priority)

    code = _fhir_codeable_concept(model.code_codings, model.code_text)
    if code:
        result["code"] = code

    if model.description:
        result["description"] = model.description

    focus = _fhir_reference(model, "focus")
    if focus:
        result["focus"] = focus

    for_ref = _fhir_reference(model, "for")
    if for_ref:
        result["for"] = for_ref

    encounter = _fhir_reference(model, "encounter")
    if encounter:
        result["encounter"] = encounter

    if model.execution_period_start or model.execution_period_end:
        period: dict = {}
        if model.execution_period_start:
            period["start"] = fhir_instant(model.execution_period_start)
        if model.execution_period_end:
            period["end"] = fhir_instant(model.execution_period_end)
        result["executionPeriod"] = period

    if model.authored_on:
        result["authoredOn"] = fhir_instant(model.authored_on)

    if model.last_modified:
        result["lastModified"] = fhir_instant(model.last_modified)

    requester = _fhir_reference(model, "requester")
    if requester:
        result["requester"] = requester

    performer_types = [
        item
        for item in (_fhir_performer_type(pt) for pt in (model.performer_types or []))
        if item is not None
    ]
    if performer_types:
        result["performerType"] = performer_types

    owner = _fhir_reference(model, "owner")
    if owner:
        result["owner"] = owner

    location = _fhir_reference(model, "location")
    if location:
        result["location"] = location

    reason_code = _fhir_codeable_concept(
        model.reason_code_codings, model.reason_code_text
    )
    if reason_code:
        result["reasonCode"] = reason_code

    reason_ref = _fhir_reference(model, "reason_reference")
    if reason_ref:
        result["reasonReference"] = reason_ref

    insurance = [
        item
        for item in (_fhir_reference_row(r) for r in (model.insurance_list or []))
        if item is not None
    ]
    if insurance:
        result["insurance"] = insurance

    notes = [
        item
        for item in (_fhir_note(n) for n in (model.notes or []))
        if item is not None
    ]
    if notes:
        result["note"] = notes

    relevant_history = [
        item
        for item in (_fhir_reference_row(r) for r in (model.relevant_history_list or []))
        if item is not None
    ]
    if relevant_history:
        result["relevantHistory"] = relevant_history

    restriction = _fhir_restriction(model)
    if restriction:
        result["restriction"] = restriction

    inputs = [
        item
        for item in (_fhir_input(inp) for inp in (model.inputs or []))
        if item is not None
    ]
    if inputs:
        result["input"] = inputs

    outputs = [
        item
        for item in (_fhir_output(out) for out in (model.outputs or []))
        if item is not None
    ]
    if outputs:
        result["output"] = outputs

    return {k: v for k, v in result.items() if v is not None}
