"""
FHIR MeasureReport document -> search index. The only write-side mapper.

MeasureReport's whole resource is stored verbatim in MeasureReportModel.content; this module
derives every *other* column and child row from it - exactly the values the FHIR R4 MeasureReport
search parameters filter on (https://www.hl7.org/fhir/R4/measurereport.html#search), nothing
more. The `group` tree has no search parameter, so none of it is indexed. See
MeasureReportModel's docstring for the parameter -> storage table; the shared builders are in
app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from app.models.measure_report import (
    REPORTER_TYPES,
    SUBJECT_TYPES,
    MeasureReportIdentifier,
    MeasureReportReference,
    MeasureReportStatus,
)
from app.repository._content_index import identifier_rows, period_bounds

from ._shared import any_typed, typed

_STATUSES = {m.value for m in MeasureReportStatus}


def _ref_columns(prefix: str, ref: dict | None, allowed: tuple[str, ...]) -> dict:
    """The index columns of one 0..1 Reference: `{prefix}_reference` (the raw string),
    `{prefix}_type`/`{prefix}_id` (a relative `Type/<id>` of an allowed type) and
    `{prefix}_identifier_system`/`_value`."""
    ref = ref if isinstance(ref, dict) else {}
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
    """Search columns on the measure_report row itself."""
    date = document.get("date")
    date_start, date_end = (
        period_bounds({"start": date, "end": date}) if date else (None, None)
    )
    period = document.get("period")
    period_start, period_end = period_bounds(
        period if isinstance(period, dict) else None
    )
    status = document.get("status")
    return {
        "status": MeasureReportStatus(status) if status in _STATUSES else None,
        "date_start": date_start,
        "date_end": date_end,
        "period_start": period_start,
        "period_end": period_end,
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("reporter", document.get("reporter"), REPORTER_TYPES),
    }


def _reference_row(param: str, ref, allowed: tuple[str, ...] | None):
    """One index row for a Reference (or the canonical `measure`, given as `{"reference": url}`)
    that has a `reference` or an `identifier`. `allowed` None means a Reference(Any)."""
    if not isinstance(ref, dict):
        return None
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = any_typed(reference) if allowed is None else typed(reference, allowed)
    return MeasureReportReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    rows = [
        _reference_row("evaluated-resource", r, None)
        for r in document.get("evaluatedResource") or []
    ]
    # `measure` is a canonical URL (a string), not a Reference object.
    if isinstance(document.get("measure"), str) and document["measure"]:
        rows.append(
            _reference_row("measure", {"reference": document["measure"]}, ("Measure",))
        )
    return [r for r in rows if r]


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by MeasureReportModel relationship name."""
    return {
        "identifiers": [
            row
            for i in document.get("identifier") or []
            for row in identifier_rows(MeasureReportIdentifier, i)
        ],
        "references": _reference_rows(document),
    }
