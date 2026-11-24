"""
FHIR Flag document -> search index. The only write-side mapper.

Flag's whole resource is stored verbatim in FlagModel.content; this module derives every *other*
column and child row from it - exactly the values the FHIR R4 Flag search parameters filter on
(https://www.hl7.org/fhir/R4/flag.html#search), nothing more. See FlagModel's docstring for the
parameter -> storage table; the shared builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from app.models.flag import (
    AUTHOR_TYPES,
    ENCOUNTER_TYPES,
    SUBJECT_TYPES,
    FlagIdentifier,
)
from app.repository._content_index import identifier_rows, period_bounds

from ._shared import typed


def _ref_columns(prefix: str, ref: dict | None, allowed: tuple[str, ...]) -> dict:
    """The index columns of one Reference: `{prefix}_reference` (the raw string),
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


def index_columns(document: dict) -> dict:
    """Search columns on the flag row itself."""
    period = document.get("period")
    start, end = period_bounds(period if isinstance(period, dict) else None)
    return {
        "period_start": start,
        "period_end": end,
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("encounter", document.get("encounter"), ENCOUNTER_TYPES),
        **_ref_columns("author", document.get("author"), AUTHOR_TYPES),
    }


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by FlagModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(FlagIdentifier, i)
        ],
    }
