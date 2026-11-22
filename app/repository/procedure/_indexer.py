"""
FHIR Procedure document -> search index. The only write-side mapper.

Procedure's whole resource is stored verbatim in ProcedureModel.content; this
module derives every *other* column and child row from it — exactly the values
the FHIR R4 Procedure search parameters filter on
(https://www.hl7.org/fhir/R4/procedure.html#search), nothing more. See
ProcedureModel's docstring for the parameter -> storage table; the shared
builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.procedure import (
    PERFORMER_TYPES,
    SUBJECT_TYPES,
    ProcedureIdentifier,
    ProcedureInstantiatesUri,
    ProcedurePerformer,
    ProcedureReference,
    ProcedureStatus,
    ProcedureToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    type_rows,
)

from ._shared import ref_type_and_id, typed


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
    """Search columns on the procedure row itself."""
    status = document.get("status")
    try:
        status = ProcedureStatus(status) if status else None
    except ValueError:
        status = None  # the validator rejects a bad code before we get here
    if document.get("performedDateTime"):
        performed_start, performed_end = _instant_bounds(document["performedDateTime"])
    else:
        performed_start, performed_end = period_bounds(document.get("performedPeriod"))
    return {
        "status": status,
        "performed_date_start": performed_start,
        "performed_date_end": performed_end,
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("encounter", document.get("encounter"), ("Encounter",)),
        **_ref_columns("location", document.get("location"), ("Location",)),
    }


def _concept_rows(param: str, concept: dict | None) -> list:
    return type_rows(partial(ProcedureToken, param=param), concept) if concept else []


def _token_rows(document: dict) -> list:
    rows = []
    rows += _concept_rows("category", document.get("category"))
    rows += _concept_rows("code", document.get("code"))
    for reason in document.get("reasonCode") or []:
        rows += _concept_rows("reason-code", reason)
    return rows


def _reference_row(param: str, ref: dict | None) -> ProcedureReference | None:
    """One index row for a Reference with a `reference` or an `identifier`
    (display-only cannot be matched by a reference search)."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = ref_type_and_id(reference, param)
    return ProcedureReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    rows = []
    for ref in document.get("basedOn") or []:
        rows.append(_reference_row("based-on", ref))
    for ref in document.get("partOf") or []:
        rows.append(_reference_row("part-of", ref))
    for ref in document.get("reasonReference") or []:
        rows.append(_reference_row("reason-reference", ref))
    # instantiatesCanonical is a list of canonical URLs (strings), not References.
    for canonical in document.get("instantiatesCanonical") or []:
        rows.append(_reference_row("instantiates-canonical", {"reference": canonical}))
    return [r for r in rows if r]


def _performer_rows(document: dict) -> list:
    rows = []
    for performer in document.get("performer") or []:
        actor = performer.get("actor") or {}
        reference = actor.get("reference")
        identifier = actor.get("identifier") or {}
        if not (reference or identifier.get("value")):
            continue
        parsed = typed(reference, PERFORMER_TYPES)
        rows.append(
            ProcedurePerformer(
                reference_reference=reference,
                reference_type=parsed[0] if parsed else None,
                reference_id=parsed[1] if parsed else None,
                reference_identifier_system=identifier.get("system"),
                reference_identifier_value=identifier.get("value"),
            )
        )
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by ProcedureModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(ProcedureIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
        "performers": _performer_rows(document),
        "instantiates_uris": [
            ProcedureInstantiatesUri(uri=u)
            for u in document.get("instantiatesUri") or []
            if u
        ],
    }
