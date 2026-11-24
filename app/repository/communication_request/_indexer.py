"""
FHIR CommunicationRequest document -> search index. The only write-side mapper.

CommunicationRequest's whole resource is stored verbatim in CommunicationRequestModel.content; this module
derives every *other* column and child row from it - exactly the values the FHIR R4 CommunicationRequest
search parameters filter on (https://www.hl7.org/fhir/R4/communicationrequest.html#search), nothing more.
See CommunicationRequestModel's docstring for the parameter -> storage table; the shared builders are in
app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.communication_request import (
    ENCOUNTER_TYPES,
    RECIPIENT_TYPES,
    REPLACES_TYPES,
    REQUESTER_TYPES,
    SENDER_TYPES,
    SUBJECT_TYPES,
    CommunicationRequestIdentifier,
    CommunicationRequestPriority,
    CommunicationRequestReference,
    CommunicationRequestStatus,
    CommunicationRequestToken,
)
from app.repository._content_index import identifier_rows, period_bounds, type_rows

from ._shared import any_typed, typed

_STATUSES = {m.value for m in CommunicationRequestStatus}
_PRIORITIES = {m.value for m in CommunicationRequestPriority}


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


def _range(value) -> tuple:
    """The half-open range a FHIR dateTime covers (None, None when absent)."""
    if not isinstance(value, str) or not value:
        return None, None
    return period_bounds({"start": value, "end": value})


def index_columns(document: dict) -> dict:
    """Search columns on the communication_request row itself."""
    status = document.get("status")
    priority = document.get("priority")
    authored = _range(document.get("authoredOn"))
    # R4's `occurrence` expression is `(CommunicationRequest.occurrence as dateTime)`: an
    # occurrencePeriod is not indexed.
    occurrence = _range(document.get("occurrenceDateTime"))
    group_identifier = document.get("groupIdentifier")
    group_identifier = group_identifier if isinstance(group_identifier, dict) else {}
    return {
        "status": CommunicationRequestStatus(status) if status in _STATUSES else None,
        "priority": CommunicationRequestPriority(priority)
        if priority in _PRIORITIES
        else None,
        "authored_start": authored[0],
        "authored_end": authored[1],
        "occurrence_start": occurrence[0],
        "occurrence_end": occurrence[1],
        "group_identifier_system": group_identifier.get("system"),
        "group_identifier_value": group_identifier.get("value"),
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("encounter", document.get("encounter"), ENCOUNTER_TYPES),
        **_ref_columns("requester", document.get("requester"), REQUESTER_TYPES),
        **_ref_columns("sender", document.get("sender"), SENDER_TYPES),
    }


def _concept(param: str, concept) -> list:
    return (
        type_rows(partial(CommunicationRequestToken, param=param), concept)
        if isinstance(concept, dict)
        else []
    )


def _token_rows(document: dict) -> list:
    rows = []
    for category in document.get("category") or []:
        rows += _concept("category", category)
    for medium in document.get("medium") or []:
        rows += _concept("medium", medium)
    return rows


def _reference_row(param: str, ref, allowed: tuple[str, ...] | None):
    """One index row for a Reference that has a `reference` or an `identifier` (display-only
    cannot be matched by a reference search). `allowed` None means a Reference(Any)."""
    if not isinstance(ref, dict):
        return None
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = any_typed(reference) if allowed is None else typed(reference, allowed)
    return CommunicationRequestReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    rows = [_reference_row("based-on", r, None) for r in document.get("basedOn") or []]
    rows += [
        _reference_row("replaces", r, REPLACES_TYPES)
        for r in document.get("replaces") or []
    ]
    rows += [
        _reference_row("recipient", r, RECIPIENT_TYPES)
        for r in document.get("recipient") or []
    ]
    return [r for r in rows if r is not None]


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by CommunicationRequestModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(CommunicationRequestIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
    }
