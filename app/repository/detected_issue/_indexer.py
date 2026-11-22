"""
FHIR DetectedIssue document -> search index. The only write-side mapper.

DetectedIssue's whole resource is stored verbatim in DetectedIssueModel.content; this module
derives every *other* column and child row from it — exactly the values the FHIR R4
DetectedIssue search parameters filter on
(https://www.hl7.org/fhir/R4/detectedissue.html#search), nothing more. See
DetectedIssueModel's docstring for the parameter -> storage table; the shared builders are in
app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.detected_issue import (
    AUTHOR_TYPES,
    DetectedIssueIdentifier,
    DetectedIssueReference,
    DetectedIssueToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    relative,
    type_rows,
)

from ._shared import any_typed, typed

# Of the three author targets, these are resources here (Device is not).
_MODELED_AUTHORS = ("Practitioner", "PractitionerRole")
# Reference(Any) targets (`implicated`, `evidence.detail`) that are existence-checked on write:
# the resources already rebuilt that an issue can involve.
_MODELED_ANY = (
    "Observation",
    "Specimen",
    "ServiceRequest",
    "Medication",
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "RelatedPerson",
    "Organization",
    "Location",
    "Encounter",
    "Appointment",
    "Condition",
    "Procedure",
    "DiagnosticReport",
    "AllergyIntolerance",
    "Immunization",
    "FamilyMemberHistory",
    "RiskAssessment",
    "ClinicalImpression",
)


def local_references(document: dict) -> list[tuple[str, str, str]]:
    """(element label, resource type, relative reference) for every local
    reference that must exist in the caller's org on write: identifier.assigner, `patient`,
    `author` (a Practitioner or PractitionerRole), every `implicated` and `evidence.detail`
    that is a rebuilt resource and every `mitigation.author`. Absolute URLs, logical
    (identifier-only) references and targets that are not resources on this server (a Device
    author, a MedicationRequest) point elsewhere and are not checked."""
    refs = []

    def add(label, reference, resource_type):
        local = relative(reference, resource_type)
        if local:
            refs.append((label, resource_type, local))

    def add_typed(label, ref, allowed):
        parsed = typed((ref or {}).get("reference"), allowed)
        if parsed:
            refs.append((label, parsed[0], ref["reference"]))

    for identifier in document.get("identifier") or []:
        add(
            "identifier.assigner",
            (identifier.get("assigner") or {}).get("reference"),
            "Organization",
        )
    add("patient", (document.get("patient") or {}).get("reference"), "Patient")
    add_typed("author", document.get("author"), _MODELED_AUTHORS)
    for ref in document.get("implicated") or []:
        add_typed("implicated", ref, _MODELED_ANY)
    for evidence in document.get("evidence") or []:
        for ref in (evidence or {}).get("detail") or []:
            add_typed("evidence.detail", ref, _MODELED_ANY)
    for mitigation in document.get("mitigation") or []:
        add_typed(
            "mitigation.author", (mitigation or {}).get("author"), _MODELED_AUTHORS
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


def _identified_bounds(document: dict):
    """The half-open range identified[x] covers: a dateTime as the range of its precision, a
    Period from its start to the instant after its end (NULL = open)."""
    value = document.get("identifiedDateTime")
    if value:
        return period_bounds({"start": value, "end": value})
    period = document.get("identifiedPeriod")
    if period:
        return period_bounds(period)
    return None, None


def index_columns(document: dict) -> dict:
    """Search columns on the detected_issue row itself."""
    start, end = _identified_bounds(document)
    return {
        "identified_start": start,
        "identified_end": end,
        **_ref_columns("patient", document.get("patient"), ("Patient",)),
        **_ref_columns("author", document.get("author"), AUTHOR_TYPES),
    }


def _token_rows(document: dict) -> list:
    concept = document.get("code")
    return (
        type_rows(partial(DetectedIssueToken, param="code"), concept) if concept else []
    )


def _reference_row(param: str, ref: dict | None) -> DetectedIssueReference | None:
    """One index row for a Reference with a `reference` or an `identifier`
    (display-only cannot be matched by a reference search). Reference(Any): any relative
    `Type/<id>` names a type."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = any_typed(reference)
    return DetectedIssueReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    rows = [_reference_row("implicated", r) for r in document.get("implicated") or []]
    return [r for r in rows if r]


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by DetectedIssueModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(DetectedIssueIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
    }
