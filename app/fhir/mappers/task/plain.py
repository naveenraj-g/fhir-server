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


def _plain_ref_row(row) -> dict:
    ref_type = fhir_enum(row.reference_type)
    return {
        "id": row.id,
        "reference_reference": row.reference_reference,
        "reference": (
            f"{ref_type}/{row.reference_id}"
            if (ref_type and row.reference_id)
            else row.reference_reference
        ),
        "reference_type": ref_type,
        "reference_id": row.reference_id,
        "reference_display": row.reference_display,
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
        "assigner_reference": i.assigner_reference,
        "assigner": (
            f"Organization/{i.assigner_id}"
            if (i.assigner_id and fhir_enum(i.assigner_type) == "Organization")
            else i.assigner_reference
        ),
        "assigner_type": fhir_enum(i.assigner_type),
        "assigner_id": i.assigner_id,
        "assigner_display": i.assigner_display,
        "assigner_identifier_use": fhir_enum(i.assigner_identifier_use),
        "assigner_identifier_type_system": i.assigner_identifier_type_system,
        "assigner_identifier_type_version": i.assigner_identifier_type_version,
        "assigner_identifier_type_code": i.assigner_identifier_type_code,
        "assigner_identifier_type_display": i.assigner_identifier_type_display,
        "assigner_identifier_type_text": i.assigner_identifier_type_text,
        "assigner_identifier_type_user_selected": i.assigner_identifier_type_user_selected,
        "assigner_identifier_system": i.assigner_identifier_system,
        "assigner_identifier_value": i.assigner_identifier_value,
        "assigner_identifier_period_start": fhir_instant(
            i.assigner_identifier_period_start
        ),
        "assigner_identifier_period_end": fhir_instant(
            i.assigner_identifier_period_end
        ),
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
        "author_reference": n.author_reference,
        "author_type": n.author_type,
        "author_id": n.author_id,
        "author_display": n.author_display,
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
        "value_reference_reference": inp.value_reference_reference,
        "value_reference": (
            f"{inp.value_reference_type}/{inp.value_reference_id}"
            if (inp.value_reference_type and inp.value_reference_id)
            else inp.value_reference_reference
        ),
        "value_reference_type": inp.value_reference_type,
        "value_reference_id": inp.value_reference_id,
        "value_reference_display": inp.value_reference_display,
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
        "value_reference_reference": out.value_reference_reference,
        "value_reference": (
            f"{out.value_reference_type}/{out.value_reference_id}"
            if (out.value_reference_type and out.value_reference_id)
            else out.value_reference_reference
        ),
        "value_reference_type": out.value_reference_type,
        "value_reference_id": out.value_reference_id,
        "value_reference_display": out.value_reference_display,
        "value_json": out.value_json,
        "tenant_id": out.tenant_id,
        "created_by": out.created_by,
        "updated_by": out.updated_by,
        "created_at": fhir_instant(out.created_at),
        "updated_at": fhir_instant(out.updated_at),
    }


def to_plain_task(model: TaskModel) -> dict:
    """Serialize a TaskModel to plain snake_case dict."""
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
        "focus_reference": model.focus_reference,
        "focus_type": model.focus_type,
        "focus_id": model.focus_id,
        "focus_display": model.focus_display,
        "for_reference": model.for_reference,
        "for_type": model.for_type,
        "for_id": model.for_id,
        "for_display": model.for_display,
        "for_": (
            f"{model.for_type}/{model.for_id}"
            if (model.for_type and model.for_id)
            else model.for_reference
        ),
        "encounter_reference": model.encounter_reference,
        "encounter_type": fhir_enum(model.encounter_type),
        "encounter_id": model.encounter_id,
        "encounter_display": model.encounter_display,
        "execution_period_start": fhir_instant(model.execution_period_start),
        "execution_period_end": fhir_instant(model.execution_period_end),
        "requester_reference": model.requester_reference,
        "requester_type": fhir_enum(model.requester_type),
        "requester_id": model.requester_id,
        "requester_display": model.requester_display,
        "owner_reference": model.owner_reference,
        "owner_type": fhir_enum(model.owner_type),
        "owner_id": model.owner_id,
        "owner_display": model.owner_display,
        "location_reference": model.location_reference,
        "location_type": fhir_enum(model.location_type),
        "location_id": model.location_id,
        "location_display": model.location_display,
        "reason_reference_reference": model.reason_reference_reference,
        "reason_reference_type": model.reason_reference_type,
        "reason_reference_id": model.reason_reference_id,
        "reason_reference_display": model.reason_reference_display,
        "group_identifier_use": fhir_enum(model.group_identifier_use),
        "group_identifier_system": model.group_identifier_system,
        "group_identifier_value": model.group_identifier_value,
        "group_identifier_period_start": fhir_instant(
            model.group_identifier_period_start
        ),
        "group_identifier_period_end": fhir_instant(
            model.group_identifier_period_end
        ),
        "group_identifier_assigner_reference": model.group_identifier_assigner_reference,
        "group_identifier_assigner_type": fhir_enum(
            model.group_identifier_assigner_type
        ),
        "group_identifier_assigner_id": model.group_identifier_assigner_id,
        "group_identifier_assigner_display": model.group_identifier_assigner_display,
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
