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


def _fhir_reference_row(row) -> dict | None:
    return _fhir_ref(
        row.reference_reference,
        row.reference_type,
        row.reference_id,
        row.reference_display,
    )


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
    assigner = _fhir_ref(
        i.assigner_reference,
        i.assigner_type,
        i.assigner_id,
        i.assigner_display,
    )
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
    assigner = _fhir_ref(
        model.group_identifier_assigner_reference,
        model.group_identifier_assigner_type,
        model.group_identifier_assigner_id,
        model.group_identifier_assigner_display,
    )
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _fhir_performer_type(pt: TaskPerformerType) -> dict | None:
    return _fhir_codeable_concept(getattr(pt, "codings", None), pt.text)


def _fhir_note(n: TaskNote) -> dict | None:
    entry: dict = {}
    if n.author_string:
        entry["authorString"] = n.author_string
    elif n.author_reference or (n.author_type and n.author_id):
        author_ref = _fhir_ref(
            n.author_reference, n.author_type, n.author_id, n.author_display
        )
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
    elif inp.value_reference_reference or (inp.value_reference_type and inp.value_reference_id):
        ref = _fhir_ref(
            inp.value_reference_reference,
            inp.value_reference_type,
            inp.value_reference_id,
            inp.value_reference_display,
        )
        if ref:
            entry["valueReference"] = ref
    elif inp.value_json is not None:
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
    elif out.value_reference_reference or (out.value_reference_type and out.value_reference_id):
        ref = _fhir_ref(
            out.value_reference_reference,
            out.value_reference_type,
            out.value_reference_id,
            out.value_reference_display,
        )
        if ref:
            entry["valueReference"] = ref
    elif out.value_json is not None:
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

    focus = _fhir_ref(
        model.focus_reference,
        model.focus_type,
        model.focus_id,
        model.focus_display,
    )
    if focus:
        result["focus"] = focus

    for_ref = _fhir_ref(
        model.for_reference,
        model.for_type,
        model.for_id,
        model.for_display,
    )
    if for_ref:
        result["for"] = for_ref

    encounter = _fhir_ref(
        model.encounter_reference,
        model.encounter_type,
        model.encounter_id,
        model.encounter_display,
    )
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

    requester = _fhir_ref(
        model.requester_reference,
        model.requester_type,
        model.requester_id,
        model.requester_display,
    )
    if requester:
        result["requester"] = requester

    performer_types = [
        item
        for item in (_fhir_performer_type(pt) for pt in (model.performer_types or []))
        if item is not None
    ]
    if performer_types:
        result["performerType"] = performer_types

    owner = _fhir_ref(
        model.owner_reference,
        model.owner_type,
        model.owner_id,
        model.owner_display,
    )
    if owner:
        result["owner"] = owner

    location = _fhir_ref(
        model.location_reference,
        model.location_type,
        model.location_id,
        model.location_display,
    )
    if location:
        result["location"] = location

    reason_code = _fhir_codeable_concept(
        model.reason_code_codings, model.reason_code_text
    )
    if reason_code:
        result["reasonCode"] = reason_code

    reason_ref = _fhir_ref(
        model.reason_reference_reference,
        model.reason_reference_type,
        model.reason_reference_id,
        model.reason_reference_display,
    )
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
