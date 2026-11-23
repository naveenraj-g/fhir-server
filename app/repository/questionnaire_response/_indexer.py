"""
FHIR QuestionnaireResponse document -> search index. The only write-side mapper.

QuestionnaireResponse's whole resource is stored verbatim in QuestionnaireResponseModel.content;
this module derives every *other* column and child row from it - exactly the values the FHIR R4
QuestionnaireResponse search parameters filter on
(https://www.hl7.org/fhir/R4/questionnaireresponse.html#search), nothing more. The `item` tree has
no search parameter, so none of it is indexed. See QuestionnaireResponseModel's docstring for the
parameter -> storage table; the shared builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from app.models.questionnaire_response import (
    AUTHOR_TYPES,
    ENCOUNTER_TYPES,
    REFERENCE_TYPES,
    SOURCE_TYPES,
    QuestionnaireResponseIdentifier,
    QuestionnaireResponseReference,
    QuestionnaireResponseStatus,
)
from app.repository._content_index import identifier_rows, period_bounds

from ._shared import any_typed, typed

_STATUSES = {m.value for m in QuestionnaireResponseStatus}


def _ref_columns(
    prefix: str, ref: dict | None, allowed: tuple[str, ...] | None
) -> dict:
    """The index columns of one 0..1 Reference: `{prefix}_reference` (the raw string),
    `{prefix}_type`/`{prefix}_id` (a relative `Type/<id>`; of an allowed type, or of any type when
    `allowed` is None - a Reference(Any)) and `{prefix}_identifier_system`/`_value`."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    parsed = any_typed(reference) if allowed is None else typed(reference, allowed)
    return {
        f"{prefix}_reference": reference,
        f"{prefix}_type": parsed[0] if parsed else None,
        f"{prefix}_id": parsed[1] if parsed else None,
        f"{prefix}_identifier_system": identifier.get("system"),
        f"{prefix}_identifier_value": identifier.get("value"),
    }


def index_columns(document: dict) -> dict:
    """Search columns on the questionnaire_response row itself."""
    authored = document.get("authored")
    start, end = (
        period_bounds({"start": authored, "end": authored})
        if authored
        else (None, None)
    )
    status = document.get("status")
    return {
        "status": QuestionnaireResponseStatus(status) if status in _STATUSES else None,
        "authored_start": start,
        "authored_end": end,
        **_ref_columns("subject", document.get("subject"), None),
        **_ref_columns("encounter", document.get("encounter"), ENCOUNTER_TYPES),
        **_ref_columns("author", document.get("author"), AUTHOR_TYPES),
        **_ref_columns("source", document.get("source"), SOURCE_TYPES),
    }


def _reference_row(
    param: str, ref: dict | None
) -> QuestionnaireResponseReference | None:
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = typed(reference, REFERENCE_TYPES[param])
    return QuestionnaireResponseReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    rows = [_reference_row("based-on", r) for r in document.get("basedOn") or []]
    rows += [_reference_row("part-of", r) for r in document.get("partOf") or []]
    # `questionnaire` is a canonical URL (a string), not a Reference object.
    if document.get("questionnaire"):
        rows.append(
            _reference_row("questionnaire", {"reference": document["questionnaire"]})
        )
    return [r for r in rows if r]


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by QuestionnaireResponseModel relationship name."""
    identifier = document.get("identifier")
    return {
        "identifiers": identifier_rows(QuestionnaireResponseIdentifier, identifier)
        if identifier
        else [],
        "references": _reference_rows(document),
    }
