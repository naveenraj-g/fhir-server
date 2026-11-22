"""
FHIR AllergyIntolerance document -> search index. The only write-side mapper.

AllergyIntolerance's whole resource is stored verbatim in
AllergyIntoleranceModel.content; this module derives every *other* column and
child row from it — exactly the values the FHIR R4 AllergyIntolerance search
parameters filter on
(https://www.hl7.org/fhir/R4/allergyintolerance.html#search), nothing more. See
AllergyIntoleranceModel's docstring for the parameter -> storage table; the
shared builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.allergy_intolerance import (
    ACTOR_TYPES,
    AllergyIntoleranceCategory,
    AllergyIntoleranceCriticality,
    AllergyIntoleranceIdentifier,
    AllergyIntoleranceReaction,
    AllergyIntoleranceReactionSeverity,
    AllergyIntoleranceToken,
    AllergyIntoleranceType,
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


def _enum(enum_cls, value):
    try:
        return enum_cls(value) if value else None
    except ValueError:
        return None  # the validator rejects a bad code before we get here


def _instant_bounds(value):
    """(start, end) of the half-open range a dateTime covers at its written
    precision; (None, None) when absent."""
    return period_bounds({"start": value, "end": value}) if value else (None, None)


def index_columns(document: dict) -> dict:
    """Search columns on the allergy_intolerance row itself."""
    recorded_start, recorded_end = _instant_bounds(document.get("recordedDate"))
    occurrence_start, occurrence_end = _instant_bounds(document.get("lastOccurrence"))
    return {
        "type": _enum(AllergyIntoleranceType, document.get("type")),
        "category": _categories(document),
        "criticality": _enum(
            AllergyIntoleranceCriticality, document.get("criticality")
        ),
        "recorded_date_start": recorded_start,
        "recorded_date_end": recorded_end,
        "last_occurrence_start": occurrence_start,
        "last_occurrence_end": occurrence_end,
        **_ref_columns("patient", document.get("patient"), ("Patient",)),
        **_ref_columns("recorder", document.get("recorder"), ACTOR_TYPES),
        **_ref_columns("asserter", document.get("asserter"), ACTOR_TYPES),
    }


def _concept_rows(param: str, concept: dict | None) -> list:
    return (
        type_rows(partial(AllergyIntoleranceToken, param=param), concept)
        if concept
        else []
    )


_CATEGORIES = {m.value for m in AllergyIntoleranceCategory}


def _categories(document: dict):
    """AllergyIntolerance.category (0..*) as enum members; None when there is none (a code outside
    the value set is dropped: the validator rejects it before we get here)."""
    values = [
        AllergyIntoleranceCategory(c)
        for c in document.get("category") or []
        if c in _CATEGORIES
    ]
    return values or None


def _token_rows(document: dict) -> list:
    rows = []
    rows += _concept_rows("clinical-status", document.get("clinicalStatus"))
    rows += _concept_rows("verification-status", document.get("verificationStatus"))
    rows += _concept_rows("code", document.get("code"))
    for reaction in document.get("reaction") or []:
        rows += _concept_rows("code", reaction.get("substance"))
        for manifestation in reaction.get("manifestation") or []:
            rows += _concept_rows("manifestation", manifestation)
        rows += _concept_rows("route", reaction.get("exposureRoute"))
    return rows


def _reaction_rows(document: dict) -> list:
    rows = []
    for reaction in document.get("reaction") or []:
        start, end = _instant_bounds(reaction.get("onset"))
        severity = _enum(AllergyIntoleranceReactionSeverity, reaction.get("severity"))
        if start or end or severity:
            rows.append(
                AllergyIntoleranceReaction(
                    onset_start=start, onset_end=end, severity=severity
                )
            )
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by AllergyIntoleranceModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(AllergyIntoleranceIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "reactions": _reaction_rows(document),
    }
