"""
FHIR ServiceRequest document -> search index. The only write-side mapper.

ServiceRequest's whole resource is stored verbatim in ServiceRequestModel.content; this
module derives every *other* column and child row from it — exactly the values the FHIR
R4 ServiceRequest search parameters filter on
(https://www.hl7.org/fhir/R4/servicerequest.html#search), nothing more. See
ServiceRequestModel's docstring for the parameter -> storage table; the shared builders are
in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create
and patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.service_request import (
    PERFORMER_TYPES,
    REQUESTER_TYPES,
    SUBJECT_TYPES,
    ServiceRequestIdentifier,
    ServiceRequestInstantiatesUri,
    ServiceRequestIntent,
    ServiceRequestPerformer,
    ServiceRequestPriority,
    ServiceRequestReference,
    ServiceRequestStatus,
    ServiceRequestToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    type_rows,
)

from ._shared import ref_type_and_id, typed

_STATUSES = {m.value for m in ServiceRequestStatus}
_INTENTS = {m.value for m in ServiceRequestIntent}
_PRIORITIES = {m.value for m in ServiceRequestPriority}


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


def _point(value):
    """The half-open range a dateTime covers at its written precision, or (None, None)."""
    return period_bounds({"start": value, "end": value}) if value else (None, None)


def _occurrence_bounds(document: dict):
    """The range occurrence[x] covers: a dateTime as the range of its precision, a Period
    from its start to the instant after its end (NULL = open), a Timing from its earliest
    event to the instant after its latest (else its `repeat.boundsPeriod`)."""
    if document.get("occurrenceDateTime"):
        return _point(document["occurrenceDateTime"])
    if document.get("occurrencePeriod"):
        return period_bounds(document["occurrencePeriod"])
    timing = document.get("occurrenceTiming")
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


def _code(value, allowed, enum):
    return enum(value) if value in allowed else None


def index_columns(document: dict) -> dict:
    """Search columns on the service_request row itself."""
    authored_start, authored_end = _point(document.get("authoredOn"))
    occurrence_start, occurrence_end = _occurrence_bounds(document)
    requisition = document.get("requisition") or {}
    return {
        "status": _code(document.get("status"), _STATUSES, ServiceRequestStatus),
        "intent": _code(document.get("intent"), _INTENTS, ServiceRequestIntent),
        "priority": _code(
            document.get("priority"), _PRIORITIES, ServiceRequestPriority
        ),
        "authored_start": authored_start,
        "authored_end": authored_end,
        "occurrence_start": occurrence_start,
        "occurrence_end": occurrence_end,
        "requisition_system": requisition.get("system"),
        "requisition_value": requisition.get("value"),
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("encounter", document.get("encounter"), ("Encounter",)),
        **_ref_columns("requester", document.get("requester"), REQUESTER_TYPES),
    }


def _concept(param: str, concept: dict | None) -> list:
    return (
        type_rows(partial(ServiceRequestToken, param=param), concept) if concept else []
    )


def _token_rows(document: dict) -> list:
    rows = []
    for category in document.get("category") or []:
        rows += _concept("category", category)
    rows += _concept("code", document.get("code"))
    for site in document.get("bodySite") or []:
        rows += _concept("body-site", site)
    rows += _concept("performer-type", document.get("performerType"))
    return rows


def _reference_row(param: str, ref: dict | None) -> ServiceRequestReference | None:
    """One index row for a Reference with a `reference` or an `identifier` (display-only
    cannot be matched by a reference search)."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = ref_type_and_id(reference, param)
    return ServiceRequestReference(
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
        ("specimen", "specimen"),
    ):
        rows += [_reference_row(param, r) for r in document.get(element) or []]
    # instantiatesCanonical is a list of canonical URLs (strings), not References.
    for canonical in document.get("instantiatesCanonical") or []:
        rows.append(_reference_row("instantiates-canonical", {"reference": canonical}))
    return [r for r in rows if r]


def _performer_rows(document: dict) -> list:
    rows = []
    for performer in document.get("performer") or []:
        performer = performer or {}
        reference = performer.get("reference")
        identifier = performer.get("identifier") or {}
        if not (reference or identifier.get("value")):
            continue
        parsed = typed(reference, PERFORMER_TYPES)
        rows.append(
            ServiceRequestPerformer(
                reference_reference=reference,
                reference_type=parsed[0] if parsed else None,
                reference_id=parsed[1] if parsed else None,
                reference_identifier_system=identifier.get("system"),
                reference_identifier_value=identifier.get("value"),
            )
        )
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by ServiceRequestModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(ServiceRequestIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
        "performers": _performer_rows(document),
        "instantiates_uris": [
            ServiceRequestInstantiatesUri(uri=u)
            for u in document.get("instantiatesUri") or []
            if u
        ],
    }
