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
    CODE_SYSTEMS,
    AllergyIntoleranceCriticality,
    AllergyIntoleranceIdentifier,
    AllergyIntoleranceReaction,
    AllergyIntoleranceToken,
    AllergyIntoleranceType,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    relative,
    type_rows,
)

from ._shared import typed

# Annotation.author[x] reference targets in R4.
_NOTE_AUTHOR_TYPES = ("Practitioner", "Patient", "RelatedPerson", "Organization")


def local_references(document: dict) -> list[tuple[str, str, str]]:
    """(element label, resource type, relative reference) for every local
    reference that must exist in the caller's org on write: identifier.assigner,
    `patient`, `encounter`, `recorder`, `asserter`, and the author of every note
    (top level and per reaction). Absolute URLs and logical (identifier-only)
    references point elsewhere and are not checked."""
    refs = []

    def add(label, reference, resource_type):
        local = relative(reference, resource_type)
        if local:
            refs.append((label, resource_type, local))

    def add_typed(label, reference, allowed):
        parsed = typed(reference, allowed)
        if parsed:
            refs.append((label, parsed[0], reference))

    for identifier in document.get("identifier") or []:
        add(
            "identifier.assigner",
            (identifier.get("assigner") or {}).get("reference"),
            "Organization",
        )
    add("patient", (document.get("patient") or {}).get("reference"), "Patient")
    add("encounter", (document.get("encounter") or {}).get("reference"), "Encounter")
    add_typed(
        "recorder", (document.get("recorder") or {}).get("reference"), ACTOR_TYPES
    )
    add_typed(
        "asserter", (document.get("asserter") or {}).get("reference"), ACTOR_TYPES
    )
    for note in document.get("note") or []:
        add_typed(
            "note.authorReference",
            (note.get("authorReference") or {}).get("reference"),
            _NOTE_AUTHOR_TYPES,
        )
    for reaction in document.get("reaction") or []:
        for note in reaction.get("note") or []:
            add_typed(
                "reaction.note.authorReference",
                (note.get("authorReference") or {}).get("reference"),
                _NOTE_AUTHOR_TYPES,
            )
    return refs


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


def _code_row(param: str, code: str | None) -> list:
    """A row for a plain `code` element (category, severity): the code with its
    fixed FHIR system."""
    return (
        [AllergyIntoleranceToken(param=param, system=CODE_SYSTEMS[param], code=code)]
        if code
        else []
    )


def _token_rows(document: dict) -> list:
    rows = []
    rows += _concept_rows("clinical-status", document.get("clinicalStatus"))
    rows += _concept_rows("verification-status", document.get("verificationStatus"))
    rows += _concept_rows("code", document.get("code"))
    for category in document.get("category") or []:
        rows += _code_row("category", category)
    for reaction in document.get("reaction") or []:
        rows += _concept_rows("code", reaction.get("substance"))
        for manifestation in reaction.get("manifestation") or []:
            rows += _concept_rows("manifestation", manifestation)
        rows += _concept_rows("route", reaction.get("exposureRoute"))
        rows += _code_row("severity", reaction.get("severity"))
    return rows


def _reaction_rows(document: dict) -> list:
    rows = []
    for reaction in document.get("reaction") or []:
        start, end = _instant_bounds(reaction.get("onset"))
        if start or end:
            rows.append(AllergyIntoleranceReaction(onset_start=start, onset_end=end))
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
