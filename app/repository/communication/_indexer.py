"""
FHIR Communication document -> search index. The only write-side mapper.

Communication's whole resource is stored verbatim in CommunicationModel.content; this module
derives every *other* column and child row from it - exactly the values the FHIR R4 Communication
search parameters filter on (https://www.hl7.org/fhir/R4/communication.html#search), nothing more.
See CommunicationModel's docstring for the parameter -> storage table; the shared builders are in
app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.communication import (
    CANONICAL_TYPES,
    ENCOUNTER_TYPES,
    RECIPIENT_TYPES,
    SENDER_TYPES,
    SUBJECT_TYPES,
    CommunicationIdentifier,
    CommunicationInstantiatesUri,
    CommunicationReference,
    CommunicationStatus,
    CommunicationToken,
)
from app.repository._content_index import identifier_rows, period_bounds, type_rows

from ._shared import any_typed, typed

_STATUSES = {m.value for m in CommunicationStatus}


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
    """Search columns on the communication row itself."""
    status = document.get("status")
    sent = _range(document.get("sent"))
    received = _range(document.get("received"))
    return {
        "status": CommunicationStatus(status) if status in _STATUSES else None,
        "sent_start": sent[0],
        "sent_end": sent[1],
        "received_start": received[0],
        "received_end": received[1],
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("encounter", document.get("encounter"), ENCOUNTER_TYPES),
        **_ref_columns("sender", document.get("sender"), SENDER_TYPES),
    }


def _concept(param: str, concept) -> list:
    return (
        type_rows(partial(CommunicationToken, param=param), concept)
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
    return CommunicationReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    rows = [_reference_row("based-on", r, None) for r in document.get("basedOn") or []]
    rows += [_reference_row("part-of", r, None) for r in document.get("partOf") or []]
    rows += [
        _reference_row("recipient", r, RECIPIENT_TYPES)
        for r in document.get("recipient") or []
    ]
    # instantiatesCanonical is a list of canonical URLs (strings), not References: the row keeps
    # the raw URL, and a relative `Type/<id>` is also resolved.
    for canonical in document.get("instantiatesCanonical") or []:
        rows.append(
            _reference_row(
                "instantiates-canonical", {"reference": canonical}, CANONICAL_TYPES
            )
        )
    return [r for r in rows if r is not None]


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by CommunicationModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(CommunicationIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
        "instantiates_uris": [
            CommunicationInstantiatesUri(uri=u)
            for u in document.get("instantiatesUri") or []
            if isinstance(u, str) and u
        ],
    }
