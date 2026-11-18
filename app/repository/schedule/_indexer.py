"""
FHIR Schedule document -> search index. The only write-side mapper.

Schedule's whole resource is stored verbatim in ScheduleModel.content; this
module derives every *other* column and child row from it — exactly the values
the FHIR R4 Schedule search parameters filter on
(https://www.hl7.org/fhir/R4/schedule.html#search), nothing more. See
ScheduleModel's docstring for the parameter -> storage table; the shared
builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.schedule import (
    TOKEN_PARAMS,
    ScheduleActor,
    ScheduleIdentifier,
    ScheduleToken,
)
from app.repository._content_index import identifier_rows, period_bounds, relative, type_rows

from ._shared import MODELED_ACTOR_TYPES, actor_type_and_id

# Relationship attributes the index owns — every one is rebuilt on each write.
INDEX_RELATIONSHIPS = ("identifiers", "tokens", "actors")


def local_references(document: dict) -> list[tuple[str, str, str]]:
    """(element label, resource type, relative reference) for every local
    reference that must exist in the caller's org on write: identifier.assigner
    and every actor of a type this server models. Absolute URLs, logical
    (identifier-only) references and Patient/RelatedPerson/Device actors point
    elsewhere and aren't checked."""
    refs = []
    for identifier in document.get("identifier") or []:
        local = relative((identifier.get("assigner") or {}).get("reference"), "Organization")
        if local:
            refs.append(("identifier.assigner", "Organization", local))
    for actor in document.get("actor") or []:
        parsed = actor_type_and_id(actor.get("reference"))
        if parsed and parsed[0] in MODELED_ACTOR_TYPES:
            refs.append(("actor", parsed[0], actor["reference"]))
    return refs


def index_columns(document: dict) -> dict:
    """Search columns on the schedule row itself."""
    start, end = period_bounds(document.get("planningHorizon"))
    return {
        "active": document.get("active"),
        "planning_horizon_start": start,
        "planning_horizon_end": end,
    }


def _actor_row(ref: dict) -> ScheduleActor | None:
    """One index row for an actor with a `reference` or an `identifier`
    (display-only can't be matched by a reference search)."""
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = actor_type_and_id(reference)
    return ScheduleActor(
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by ScheduleModel relationship name."""
    tokens = []
    for param, element in TOKEN_PARAMS.items():
        model = partial(ScheduleToken, param=param)
        for concept in document.get(element) or []:
            tokens.extend(type_rows(model, concept))
    return {
        "identifiers": [r for i in document.get("identifier") or [] for r in identifier_rows(ScheduleIdentifier, i)],
        "tokens": tokens,
        "actors": [r for a in document.get("actor") or [] if (r := _actor_row(a))],
    }
