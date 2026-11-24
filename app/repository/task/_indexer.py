"""
FHIR Task document -> search index. The only write-side mapper.

Task's whole resource is stored verbatim in TaskModel.content; this module derives every *other*
column and child row from it - exactly the values the FHIR R4 Task search parameters filter on
(https://www.hl7.org/fhir/R4/task.html#search), nothing more. See TaskModel's docstring for the
parameter -> storage table; the shared builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.task import (
    ENCOUNTER_TYPES,
    OWNER_TYPES,
    PART_OF_TYPES,
    REQUESTER_TYPES,
    TaskIdentifier,
    TaskIntent,
    TaskPriority,
    TaskReference,
    TaskStatus,
    TaskToken,
)
from app.repository._content_index import identifier_rows, period_bounds, type_rows

from ._shared import any_typed, typed

_STATUSES = {m.value for m in TaskStatus}
_INTENTS = {m.value for m in TaskIntent}
_PRIORITIES = {m.value for m in TaskPriority}


def _ref_columns(
    prefix: str, ref: dict | None, allowed: tuple[str, ...] | None
) -> dict:
    """The index columns of one 0..1 Reference: `{prefix}_reference` (the raw string),
    `{prefix}_type`/`{prefix}_id` (a relative `Type/<id>`; any type when `allowed` is None, as for
    a Reference(Any)) and `{prefix}_identifier_system`/`_value`."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    parsed = any_typed(reference) if allowed is None else typed(reference, allowed)
    return {
        f"{prefix}_reference": reference,
        f"{prefix}_type": parsed[0] if parsed else None,
        f"{prefix}_id": parsed[1] if parsed else None,
        f"{prefix}_identifier_system": identifier.get("system"),
        f"{prefix}_identifier_value": identifier.get("value"),
    }


def _range(value) -> tuple:
    """The half-open range a FHIR date/dateTime covers (None, None when absent)."""
    if not isinstance(value, str) or not value:
        return None, None
    return period_bounds({"start": value, "end": value})


def index_columns(document: dict) -> dict:
    """Search columns on the task row itself."""
    status, intent, priority = (
        document.get("status"),
        document.get("intent"),
        document.get("priority"),
    )
    authored = _range(document.get("authoredOn"))
    modified = _range(document.get("lastModified"))
    period = period_bounds(
        document.get("executionPeriod")
        if isinstance(document.get("executionPeriod"), dict)
        else None
    )
    group = document.get("groupIdentifier") or {}
    return {
        "status": TaskStatus(status) if status in _STATUSES else None,
        "intent": TaskIntent(intent) if intent in _INTENTS else None,
        "priority": TaskPriority(priority) if priority in _PRIORITIES else None,
        "authored_start": authored[0],
        "authored_end": authored[1],
        "modified_start": modified[0],
        "modified_end": modified[1],
        "period_start": period[0],
        "period_end": period[1],
        "group_identifier_system": group.get("system"),
        "group_identifier_value": group.get("value"),
        **_ref_columns("for", document.get("for"), None),
        **_ref_columns("focus", document.get("focus"), None),
        **_ref_columns("encounter", document.get("encounter"), ENCOUNTER_TYPES),
        **_ref_columns("requester", document.get("requester"), REQUESTER_TYPES),
        **_ref_columns("owner", document.get("owner"), OWNER_TYPES),
    }


def _concept(param: str, concept: dict | None) -> list:
    return (
        type_rows(partial(TaskToken, param=param), concept)
        if isinstance(concept, dict)
        else []
    )


def _token_rows(document: dict) -> list:
    rows = _concept("business-status", document.get("businessStatus"))
    rows += _concept("code", document.get("code"))
    for performer_type in document.get("performerType") or []:
        rows += _concept("performer", performer_type)
    return rows


def _reference_row(param: str, ref: dict | None):
    """One index row for a Reference that has a `reference` or an `identifier` (display-only
    cannot be matched by a reference search)."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = (
        any_typed(reference) if param == "based-on" else typed(reference, PART_OF_TYPES)
    )
    return TaskReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    rows = [_reference_row("based-on", r) for r in document.get("basedOn") or []]
    rows += [_reference_row("part-of", r) for r in document.get("partOf") or []]
    return [r for r in rows if r is not None]


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by TaskModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(TaskIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
    }
