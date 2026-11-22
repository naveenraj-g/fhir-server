"""
FHIR Immunization document -> search index. The only write-side mapper.

Immunization's whole resource is stored verbatim in ImmunizationModel.content;
this module derives every *other* column and child row from it — exactly the
values the FHIR R4 Immunization search parameters filter on
(https://www.hl7.org/fhir/R4/immunization.html#search), nothing more. See
ImmunizationModel's docstring for the parameter -> storage table; the shared
builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from functools import partial

from app.fhir.search import normalize
from app.models.immunization import (
    PERFORMER_TYPES,
    REASON_TYPES,
    ImmunizationIdentifier,
    ImmunizationPerformer,
    ImmunizationProtocol,
    ImmunizationReaction,
    ImmunizationReasonReference,
    ImmunizationStatus,
    ImmunizationToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    type_rows,
)

from ._shared import typed


def _ref_columns(prefix: str, ref: dict | None, allowed: tuple[str, ...]) -> dict:
    """The index columns of one 0..1 Reference: `{prefix}_reference` (the raw
    string), `{prefix}_type`/`{prefix}_id` (a relative `Type/<id>` of an
    allowed type) and `{prefix}_identifier_system`/`_value`."""
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


def _instant_bounds(value):
    """(start, end) of the half-open range a dateTime covers at its written
    precision; (None, None) when absent."""
    return period_bounds({"start": value, "end": value}) if value else (None, None)


def index_columns(document: dict) -> dict:
    """Search columns on the immunization row itself."""
    status = document.get("status")
    try:
        status = ImmunizationStatus(status) if status else None
    except ValueError:
        status = None  # the validator rejects a bad code before we get here
    start, end = _instant_bounds(document.get("occurrenceDateTime"))
    lot = document.get("lotNumber")
    return {
        "status": status,
        "occurrence_date_start": start,
        "occurrence_date_end": end,
        "lot_number": lot,
        "lot_number_norm": normalize(lot) if lot else None,
        **_ref_columns("patient", document.get("patient"), ("Patient",)),
        **_ref_columns("location", document.get("location"), ("Location",)),
        **_ref_columns("manufacturer", document.get("manufacturer"), ("Organization",)),
    }


def _concept_rows(param: str, concept: dict | None) -> list:
    return (
        type_rows(partial(ImmunizationToken, param=param), concept) if concept else []
    )


def _token_rows(document: dict) -> list:
    rows = []
    for concept in document.get("reasonCode") or []:
        rows += _concept_rows("reason-code", concept)
    rows += _concept_rows("status-reason", document.get("statusReason"))
    for protocol in document.get("protocolApplied") or []:
        for concept in (protocol or {}).get("targetDisease") or []:
            rows += _concept_rows("target-disease", concept)
    rows += _concept_rows("vaccine-code", document.get("vaccineCode"))
    return rows


def _protocol_rows(document: dict) -> list:
    return [
        ImmunizationProtocol(series=p["series"], series_norm=normalize(p["series"]))
        for p in document.get("protocolApplied") or []
        if (p or {}).get("series")
    ]


def _reaction_rows(document: dict) -> list:
    rows = []
    for reaction in document.get("reaction") or []:
        reaction = reaction or {}
        detail = reaction.get("detail") or {}
        reference = detail.get("reference")
        identifier = detail.get("identifier") or {}
        start, end = _instant_bounds(reaction.get("date"))
        if not (reference or identifier.get("value") or start):
            continue
        parsed = typed(reference, ("Observation",))
        rows.append(
            ImmunizationReaction(
                detail_reference=reference,
                detail_type=parsed[0] if parsed else None,
                detail_id=parsed[1] if parsed else None,
                detail_identifier_system=identifier.get("system"),
                detail_identifier_value=identifier.get("value"),
                date_start=start,
                date_end=end,
            )
        )
    return rows


def _reference_row(model, ref: dict | None, allowed: tuple[str, ...]):
    """One index row for a Reference with a `reference` or an `identifier`
    (display-only cannot be matched by a reference search)."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = typed(reference, allowed)
    return model(
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _performer_rows(document: dict) -> list:
    rows = [
        _reference_row(ImmunizationPerformer, (p or {}).get("actor"), PERFORMER_TYPES)
        for p in document.get("performer") or []
    ]
    return [r for r in rows if r]


def _reason_reference_rows(document: dict) -> list:
    rows = [
        _reference_row(ImmunizationReasonReference, r, REASON_TYPES)
        for r in document.get("reasonReference") or []
    ]
    return [r for r in rows if r]


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by ImmunizationModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(ImmunizationIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "protocols": _protocol_rows(document),
        "reactions": _reaction_rows(document),
        "performers": _performer_rows(document),
        "reason_references": _reason_reference_rows(document),
    }
