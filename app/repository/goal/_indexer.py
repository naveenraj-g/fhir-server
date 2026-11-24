"""
FHIR Goal document -> search index. The only write-side mapper.

Goal's whole resource is stored verbatim in GoalModel.content; this module derives every *other*
column and child row from it - exactly the values the FHIR R4 Goal search parameters filter on
(https://www.hl7.org/fhir/R4/goal.html#search), nothing more. See GoalModel's docstring for the
parameter -> storage table; the shared builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.goal import (
    SUBJECT_TYPES,
    GoalIdentifier,
    GoalLifecycleStatus,
    GoalTarget,
    GoalToken,
)
from app.repository._content_index import identifier_rows, period_bounds, type_rows

from ._shared import typed

_STATUSES = {m.value for m in GoalLifecycleStatus}


def _ref_columns(prefix: str, ref: dict | None, allowed: tuple[str, ...]) -> dict:
    """The index columns of one 0..1 Reference: `{prefix}_reference` (the raw string),
    `{prefix}_type`/`{prefix}_id` (a relative `Type/<id>` of an allowed type) and
    `{prefix}_identifier_system`/`_value`."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    parsed = typed(reference, allowed)
    return {
        f"{prefix}_reference": reference,
        f"{prefix}_type": parsed[0] if parsed else None,
        f"{prefix}_id": parsed[1] if parsed else None,
        f"{prefix}_identifier_system": identifier.get("system"),
        f"{prefix}_identifier_value": identifier.get("value"),
    }


def _date_range(value) -> tuple:
    """The half-open range a FHIR date covers (None, None when absent)."""
    if not isinstance(value, str) or not value:
        return None, None
    return period_bounds({"start": value, "end": value})


def index_columns(document: dict) -> dict:
    """Search columns on the goal row itself."""
    status = document.get("lifecycleStatus")
    start, end = _date_range(document.get("startDate"))
    return {
        "lifecycle_status": GoalLifecycleStatus(status)
        if status in _STATUSES
        else None,
        "start_start": start,
        "start_end": end,
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
    }


def _concept(param: str, concept: dict | None) -> list:
    return (
        type_rows(partial(GoalToken, param=param), concept)
        if isinstance(concept, dict)
        else []
    )


def _token_rows(document: dict) -> list:
    rows = _concept("achievement-status", document.get("achievementStatus"))
    for category in document.get("category") or []:
        rows += _concept("category", category)
    return rows


def _target_rows(document: dict) -> list:
    rows = []
    for target in document.get("target") or []:
        start, end = _date_range((target or {}).get("dueDate"))
        if start is not None:
            rows.append(GoalTarget(due_start=start, due_end=end))
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by GoalModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(GoalIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "targets": _target_rows(document),
    }
