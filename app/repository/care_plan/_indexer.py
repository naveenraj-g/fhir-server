"""
FHIR CarePlan document -> search index. The only write-side mapper.

CarePlan's whole resource is stored verbatim in CarePlanModel.content; this module derives every
*other* column and child row from it - exactly the values the FHIR R4 CarePlan search parameters
filter on (https://www.hl7.org/fhir/R4/careplan.html#search), nothing more. See CarePlanModel's
docstring for the parameter -> storage table; the shared builders are in
app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.care_plan import (
    ACTIVITY_REFERENCE_TYPES,
    ENCOUNTER_TYPES,
    PERFORMER_TYPES,
    SUBJECT_TYPES,
    CarePlanActivity,
    CarePlanIdentifier,
    CarePlanInstantiatesUri,
    CarePlanIntent,
    CarePlanPerformer,
    CarePlanReference,
    CarePlanStatus,
    CarePlanToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    type_rows,
)

from ._shared import ref_type_and_id, typed

_STATUSES = {m.value for m in CarePlanStatus}
_INTENTS = {m.value for m in CarePlanIntent}


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


def index_columns(document: dict) -> dict:
    """Search columns on the care_plan row itself."""
    start, end = period_bounds(document.get("period"))
    status, intent = document.get("status"), document.get("intent")
    return {
        "status": CarePlanStatus(status) if status in _STATUSES else None,
        "intent": CarePlanIntent(intent) if intent in _INTENTS else None,
        "period_start": start,
        "period_end": end,
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("encounter", document.get("encounter"), ENCOUNTER_TYPES),
    }


def _concept(param: str, concept: dict | None) -> list:
    return type_rows(partial(CarePlanToken, param=param), concept) if concept else []


def _token_rows(document: dict) -> list:
    rows = []
    for category in document.get("category") or []:
        rows += _concept("category", category)
    for activity in document.get("activity") or []:
        rows += _concept(
            "activity-code", ((activity or {}).get("detail") or {}).get("code")
        )
    return rows


def _reference_row(param: str, ref: dict | None) -> CarePlanReference | None:
    """One index row for a Reference with a `reference` or an `identifier` (display-only cannot be
    matched by a reference search)."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = ref_type_and_id(reference, param)
    return CarePlanReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    rows = []
    for param, element in (
        ("based-on", "basedOn"),
        ("replaces", "replaces"),
        ("part-of", "partOf"),
        ("care-team", "careTeam"),
        ("condition", "addresses"),
        ("goal", "goal"),
    ):
        rows += [_reference_row(param, r) for r in document.get(element) or []]
    # instantiatesCanonical is a list of canonical URLs (strings), not References.
    for canonical in document.get("instantiatesCanonical") or []:
        rows.append(_reference_row("instantiates-canonical", {"reference": canonical}))
    return [r for r in rows if r]


def _performer_rows(document: dict) -> list:
    rows = []
    for activity in document.get("activity") or []:
        detail = (activity or {}).get("detail") or {}
        for performer in detail.get("performer") or []:
            performer = performer or {}
            reference = performer.get("reference")
            identifier = performer.get("identifier") or {}
            if not (reference or identifier.get("value")):
                continue
            parsed = typed(reference, PERFORMER_TYPES)
            rows.append(
                CarePlanPerformer(
                    reference_reference=reference,
                    reference_type=parsed[0] if parsed else None,
                    reference_id=parsed[1] if parsed else None,
                    reference_identifier_system=identifier.get("system"),
                    reference_identifier_value=identifier.get("value"),
                )
            )
    return rows


def _point(value):
    """The half-open range a dateTime covers at its written precision, or (None, None)."""
    return period_bounds({"start": value, "end": value}) if value else (None, None)


def _scheduled_bounds(detail: dict):
    """The range activity.detail.scheduled[x] covers: a Period from its start to the instant
    after its end (NULL = open), a Timing from its earliest event to the instant after its latest
    (else its `repeat.boundsPeriod`). A `scheduledString` is not a date."""
    if detail.get("scheduledPeriod"):
        return period_bounds(detail["scheduledPeriod"])
    timing = detail.get("scheduledTiming")
    if timing:
        starts, ends = [], []
        for event in timing.get("event") or []:
            start, end = _point(event)
            if start:
                starts.append(start)
            if end:
                ends.append(end)
        if starts:
            return min(starts), max(ends)
        return period_bounds((timing.get("repeat") or {}).get("boundsPeriod"))
    return None, None


def _activity_rows(document: dict) -> list:
    rows = []
    for activity in document.get("activity") or []:
        activity = activity or {}
        ref = activity.get("reference") or {}
        reference = ref.get("reference")
        identifier = ref.get("identifier") or {}
        start, end = _scheduled_bounds(activity.get("detail") or {})
        if not (reference or identifier.get("value") or start or end):
            continue
        parsed = typed(reference, ACTIVITY_REFERENCE_TYPES)
        rows.append(
            CarePlanActivity(
                reference_reference=reference,
                reference_type=parsed[0] if parsed else None,
                reference_id=parsed[1] if parsed else None,
                reference_identifier_system=identifier.get("system"),
                reference_identifier_value=identifier.get("value"),
                scheduled_start=start,
                scheduled_end=end,
            )
        )
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by CarePlanModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(CarePlanIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
        "performers": _performer_rows(document),
        "instantiates_uris": [
            CarePlanInstantiatesUri(uri=u)
            for u in document.get("instantiatesUri") or []
            if u
        ],
        "activities": _activity_rows(document),
    }
