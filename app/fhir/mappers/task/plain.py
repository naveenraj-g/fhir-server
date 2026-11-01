from __future__ import annotations

from typing import TYPE_CHECKING

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


def _plain_coding(c) -> dict:
    return {
        "id": c.id,
        "system": c.system,
        "version": c.version,
        "code": c.code,
        "display": c.display,
        "user_selected": c.user_selected,
        "tenant_id": c.tenant_id,
        "created_by": c.created_by,
        "updated_by": c.updated_by,
        "created_at": fhir_instant(c.created_at),
        "updated_at": fhir_instant(c.updated_at),
    }


def _plain_reference_fields(obj, prefix: str) -> dict:
    raw_reference = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    computed = raw_reference or (
        f"{fhir_enum(ref_type)}/{ref_id}" if ref_type and ref_id else None
    )
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)
    return {
        f"{prefix}_reference": raw_reference,
        prefix: computed,
        f"{prefix}_type": fhir_enum(ref_type),
        f"{prefix}_id": ref_id,
        f"{prefix}_display": getattr(obj, f"{prefix}_display", None),
        f"{prefix}_identifier_use": fhir_enum(
            getattr(obj, f"{prefix}_identifier_use", None)
        ),
        f"{prefix}_identifier_type_system": getattr(
            obj, f"{prefix}_identifier_type_system", None
        ),
        f"{prefix}_identifier_type_version": getattr(
            obj, f"{prefix}_identifier_type_version", None
        ),
        f"{prefix}_identifier_type_code": getattr(
            obj, f"{prefix}_identifier_type_code", None
        ),
        f"{prefix}_identifier_type_display": getattr(
            obj, f"{prefix}_identifier_type_display", None
        ),
        f"{prefix}_identifier_type_text": getattr(
            obj, f"{prefix}_identifier_type_text", None
        ),
        f"{prefix}_identifier_type_user_selected": getattr(
            obj, f"{prefix}_identifier_type_user_selected", None
        ),
        f"{prefix}_identifier_system": getattr(
            obj, f"{prefix}_identifier_system", None
        ),
        f"{prefix}_identifier_value": getattr(obj, f"{prefix}_identifier_value", None),
        f"{prefix}_identifier_period_start": fhir_instant(id_period_start)
        if id_period_start
        else None,
        f"{prefix}_identifier_period_end": fhir_instant(id_period_end)
        if id_period_end
        else None,
    }


def _plain_ref_row(row) -> dict:
    return {
        "id": row.id,
        **_plain_reference_fields(row, "reference"),
        "tenant_id": row.tenant_id,
        "created_by": row.created_by,
        "updated_by": row.updated_by,
        "created_at": fhir_instant(row.created_at),
        "updated_at": fhir_instant(row.updated_at),
    }


def _plain_identifier(i: TaskIdentifier) -> dict:
    return {
        "id": i.id,
        "use": fhir_enum(i.use),
        "type_text": i.type_text,
        "type_codings": [_plain_coding(c) for c in (i.type_codings or [])],
        "system": i.system,
        "value": i.value,
        "period_start": fhir_instant(i.period_start),
        "period_end": fhir_instant(i.period_end),
        **_plain_reference_fields(i, "assigner"),
        "tenant_id": i.tenant_id,
        "created_by": i.created_by,
        "updated_by": i.updated_by,
        "created_at": fhir_instant(i.created_at),
        "updated_at": fhir_instant(i.updated_at),
    }


def _plain_performer_type(pt: TaskPerformerType) -> dict:
    return {
        "id": pt.id,
        "text": pt.text,
        "codings": [_plain_coding(c) for c in (pt.codings or [])],
        "tenant_id": pt.tenant_id,
        "created_by": pt.created_by,
        "updated_by": pt.updated_by,
        "created_at": fhir_instant(pt.created_at),
        "updated_at": fhir_instant(pt.updated_at),
    }


def _plain_note(n: TaskNote) -> dict:
    return {
        "id": n.id,
        "author_string": n.author_string,
        **_plain_reference_fields(n, "author"),
        "time": fhir_instant(n.time),
        "text": n.text,
        "tenant_id": n.tenant_id,
        "created_by": n.created_by,
        "updated_by": n.updated_by,
        "created_at": fhir_instant(n.created_at),
        "updated_at": fhir_instant(n.updated_at),
    }


def _plain_input(inp: TaskInput) -> dict:
    return {
        "id": inp.id,
        "type_text": inp.type_text,
        "type_codings": [_plain_coding(c) for c in (inp.type_codings or [])],
        "value_string": inp.value_string,
        "value_boolean": inp.value_boolean,
        "value_integer": inp.value_integer,
        "value_decimal": float(inp.value_decimal) if inp.value_decimal is not None else None,
        "value_date": _format_date(inp.value_date) if inp.value_date else None,
        "value_date_time": fhir_instant(inp.value_date_time),
        "value_time": str(inp.value_time) if inp.value_time else None,
        "value_uri": inp.value_uri,
        "value_code": inp.value_code,
        **_plain_reference_fields(inp, "value_reference"),
        "value_json": inp.value_json,
        "tenant_id": inp.tenant_id,
        "created_by": inp.created_by,
        "updated_by": inp.updated_by,
        "created_at": fhir_instant(inp.created_at),
        "updated_at": fhir_instant(inp.updated_at),
    }


def _plain_output(out: TaskOutput) -> dict:
    return {
        "id": out.id,
        "type_text": out.type_text,
        "type_codings": [_plain_coding(c) for c in (out.type_codings or [])],
        "value_string": out.value_string,
        "value_boolean": out.value_boolean,
        "value_integer": out.value_integer,
        "value_decimal": float(out.value_decimal) if out.value_decimal is not None else None,
        "value_date": _format_date(out.value_date) if out.value_date else None,
        "value_date_time": fhir_instant(out.value_date_time),
        "value_time": str(out.value_time) if out.value_time else None,
        "value_uri": out.value_uri,
        "value_code": out.value_code,
        **_plain_reference_fields(out, "value_reference"),
        "value_json": out.value_json,
        "tenant_id": out.tenant_id,
        "created_by": out.created_by,
        "updated_by": out.updated_by,
        "created_at": fhir_instant(out.created_at),
        "updated_at": fhir_instant(out.updated_at),
    }


def to_plain_task(model: TaskModel) -> dict:
    """Serialize a TaskModel to plain snake_case dict."""
    for_dict = _plain_reference_fields(model, "for")
    return {
        "id": model.task_id,
        "status": fhir_enum(model.status),
        "intent": fhir_enum(model.intent),
        "priority": fhir_enum(model.priority) if model.priority else None,
        "description": model.description,
        "instantiates_canonical": model.instantiates_canonical,
        "instantiates_uri": model.instantiates_uri,
        "authored_on": fhir_instant(model.authored_on),
        "last_modified": fhir_instant(model.last_modified),
        "code_text": model.code_text,
        "code_codings": [_plain_coding(c) for c in (model.code_codings or [])],
        "status_reason_text": model.status_reason_text,
        "status_reason_codings": [
            _plain_coding(c) for c in (model.status_reason_codings or [])
        ],
        "business_status_text": model.business_status_text,
        "business_status_codings": [
            _plain_coding(c) for c in (model.business_status_codings or [])
        ],
        "reason_code_text": model.reason_code_text,
        "reason_code_codings": [
            _plain_coding(c) for c in (model.reason_code_codings or [])
        ],
        **_plain_reference_fields(model, "focus"),
        **for_dict,
        "for_": for_dict.get("for"),
        **_plain_reference_fields(model, "encounter"),
        "execution_period_start": fhir_instant(model.execution_period_start),
        "execution_period_end": fhir_instant(model.execution_period_end),
        **_plain_reference_fields(model, "requester"),
        **_plain_reference_fields(model, "owner"),
        **_plain_reference_fields(model, "location"),
        **_plain_reference_fields(model, "reason_reference"),
        "group_identifier_use": fhir_enum(model.group_identifier_use),
        "group_identifier_system": model.group_identifier_system,
        "group_identifier_value": model.group_identifier_value,
        "group_identifier_period_start": fhir_instant(
            model.group_identifier_period_start
        ),
        "group_identifier_period_end": fhir_instant(
            model.group_identifier_period_end
        ),
        **_plain_reference_fields(model, "group_identifier_assigner"),
        "restriction_repetitions": model.restriction_repetitions,
        "restriction_period_start": fhir_instant(model.restriction_period_start),
        "restriction_period_end": fhir_instant(model.restriction_period_end),
        "extension": list(model.extension) if model.extension else [],
        "tenant_id": model.tenant_id,
        "created_by": model.created_by,
        "updated_by": model.updated_by,
        "created_at": fhir_instant(model.created_at),
        "updated_at": fhir_instant(model.updated_at),
        "identifiers": [_plain_identifier(i) for i in (model.identifiers or [])],
        "performer_types": [
            _plain_performer_type(pt) for pt in (model.performer_types or [])
        ],
        "based_on_list": [_plain_ref_row(r) for r in (model.based_on_list or [])],
        "part_of_list": [_plain_ref_row(r) for r in (model.part_of_list or [])],
        "insurance_list": [_plain_ref_row(r) for r in (model.insurance_list or [])],
        "relevant_history_list": [
            _plain_ref_row(r) for r in (model.relevant_history_list or [])
        ],
        "restriction_recipients": [
            _plain_ref_row(r) for r in (model.restriction_recipients or [])
        ],
        "notes": [_plain_note(n) for n in (model.notes or [])],
        "inputs": [_plain_input(inp) for inp in (model.inputs or [])],
        "outputs": [_plain_output(out) for out in (model.outputs or [])],
    }
