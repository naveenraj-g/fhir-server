"""
FHIR ImmunizationRecommendation document -> search index. The only write-side mapper.

ImmunizationRecommendation's whole resource is stored verbatim in
ImmunizationRecommendationModel.content; this module derives every *other* column
and child row from it — exactly the values the FHIR R4 ImmunizationRecommendation
search parameters filter on
(https://www.hl7.org/fhir/R4/immunizationrecommendation.html#search), nothing more.
See ImmunizationRecommendationModel's docstring for the parameter -> storage table;
the shared builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.immunization_recommendation import (
    SUPPORT_TYPES,
    ImmunizationRecommendationIdentifier,
    ImmunizationRecommendationReference,
    ImmunizationRecommendationToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    relative,
    type_rows,
)

from ._shared import any_typed, typed

# Both `support` targets (Immunization, ImmunizationEvaluation) are resources here.
_MODELED_SUPPORT = ("Immunization", "ImmunizationEvaluation")
# Reference(Any) `supportingPatientInformation` targets that are existence-checked on write:
# the resources already rebuilt that a piece of patient information can be.
_MODELED_INFORMATION = (
    "Observation",
    "Specimen",
    "ServiceRequest",
    "Medication",
    "MedicationRequest",
    "Group",
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
)


def local_references(document: dict) -> list[tuple[str, str, str]]:
    """(element label, resource type, relative reference) for every local
    reference that must exist in the caller's org on write: identifier.assigner,
    `patient`, `authority`, every `supportingImmunization` that is an Immunization
    and every `supportingPatientInformation` that is a rebuilt resource. Absolute
    URLs, logical (identifier-only) references and targets that are not resources on
    this server (an ImmunizationEvaluation) point elsewhere and are not
    checked."""
    refs = []

    def add(label, reference, resource_type):
        local = relative(reference, resource_type)
        if local:
            refs.append((label, resource_type, local))

    for identifier in document.get("identifier") or []:
        add(
            "identifier.assigner",
            (identifier.get("assigner") or {}).get("reference"),
            "Organization",
        )
    add("patient", (document.get("patient") or {}).get("reference"), "Patient")
    add("authority", (document.get("authority") or {}).get("reference"), "Organization")
    for recommendation in document.get("recommendation") or []:
        recommendation = recommendation or {}
        for ref in recommendation.get("supportingImmunization") or []:
            parsed = typed((ref or {}).get("reference"), _MODELED_SUPPORT)
            if parsed:
                refs.append(("supportingImmunization", parsed[0], ref["reference"]))
        for ref in recommendation.get("supportingPatientInformation") or []:
            parsed = typed((ref or {}).get("reference"), _MODELED_INFORMATION)
            if parsed:
                refs.append(
                    ("supportingPatientInformation", parsed[0], ref["reference"])
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


def index_columns(document: dict) -> dict:
    """Search columns on the immunization_recommendation row itself."""
    value = document.get("date")
    start, end = (
        period_bounds({"start": value, "end": value}) if value else (None, None)
    )
    return {
        "date_start": start,
        "date_end": end,
        **_ref_columns("patient", document.get("patient"), ("Patient",)),
    }


def _concept_rows(param: str, concept: dict | None) -> list:
    return (
        type_rows(partial(ImmunizationRecommendationToken, param=param), concept)
        if concept
        else []
    )


def _token_rows(document: dict) -> list:
    rows = []
    for recommendation in document.get("recommendation") or []:
        recommendation = recommendation or {}
        rows += _concept_rows("status", recommendation.get("forecastStatus"))
        rows += _concept_rows("target-disease", recommendation.get("targetDisease"))
        for concept in recommendation.get("vaccineCode") or []:
            rows += _concept_rows("vaccine-type", concept)
    return rows


def _reference_row(
    param: str, ref: dict | None
) -> ImmunizationRecommendationReference | None:
    """One index row for a Reference with a `reference` or an `identifier`
    (display-only cannot be matched by a reference search)."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    # Any relative `Type/<id>` names a type (`information` is Reference(Any)); `support`
    # only the two R4 targets.
    parsed = (
        any_typed(reference)
        if param == "information"
        else typed(reference, SUPPORT_TYPES)
    )
    return ImmunizationRecommendationReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    rows = []
    for recommendation in document.get("recommendation") or []:
        recommendation = recommendation or {}
        rows += [
            _reference_row("support", r)
            for r in recommendation.get("supportingImmunization") or []
        ]
        rows += [
            _reference_row("information", r)
            for r in recommendation.get("supportingPatientInformation") or []
        ]
    return [r for r in rows if r]


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by ImmunizationRecommendationModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(ImmunizationRecommendationIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
    }
