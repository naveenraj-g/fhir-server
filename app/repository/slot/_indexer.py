"""
FHIR Slot document -> search index. The only write-side mapper.

Slot's whole resource is stored verbatim in SlotModel.content; this module
derives every *other* column and child row from it — exactly the values the
FHIR R4 Slot search parameters filter on
(https://www.hl7.org/fhir/R4/slot.html#search), nothing more. See SlotModel's
docstring for the parameter -> storage table; the shared builders are in
app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from datetime import UTC, datetime
from functools import partial

from app.fhir.search.values import parse_date
from app.models.slot import TOKEN_PARAMS, SlotIdentifier, SlotStatus, SlotToken
from app.repository._content_index import identifier_rows, reference_columns, relative, type_rows

from ._shared import _parse_schedule_ref

# Relationship attributes the index owns — every one is rebuilt on each write.
INDEX_RELATIONSHIPS = ("identifiers", "tokens")


def local_references(document: dict) -> list[tuple[str, str, str]]:
    """(element label, resource type, relative reference) for every local
    reference that must exist in the caller's org on write: the Schedule and
    identifier.assigner. An absolute URL or a logical (identifier-only)
    reference points elsewhere and isn't checked."""
    refs = []
    local = relative((document.get("schedule") or {}).get("reference"), "Schedule")
    if local:
        refs.append(("schedule", "Schedule", local))
    for identifier in document.get("identifier") or []:
        local = relative((identifier.get("assigner") or {}).get("reference"), "Organization")
        if local:
            refs.append(("identifier.assigner", "Organization", local))
    return refs


def _instant(value) -> datetime | None:
    """Slot.start as a UTC datetime (None if absent or unparseable — a bad
    instant is the validator's to reject)."""
    if not value:
        return None
    try:
        return parse_date(str(value)).low.astimezone(UTC)
    except Exception:
        return None


def index_columns(document: dict) -> dict:
    """Search columns on the slot row itself."""
    status = document.get("status")
    try:
        status = SlotStatus(status) if status else None
    except ValueError:
        status = None  # the validator rejects a bad code before we get here
    return {
        "status": status,
        "start": _instant(document.get("start")),
        **reference_columns("schedule", document.get("schedule"), "Schedule", _parse_schedule_ref),
    }


def _concepts(value) -> list[dict]:
    """A CodeableConcept element as a list: `appointmentType` is 0..1 (an
    object), the others 0..* (a list)."""
    if isinstance(value, dict):
        return [value]
    return list(value or [])


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by SlotModel relationship name."""
    tokens = []
    for param, element in TOKEN_PARAMS.items():
        model = partial(SlotToken, param=param)
        for concept in _concepts(document.get(element)):
            tokens.extend(type_rows(model, concept))
    return {
        "identifiers": [r for i in document.get("identifier") or [] for r in identifier_rows(SlotIdentifier, i)],
        "tokens": tokens,
    }
