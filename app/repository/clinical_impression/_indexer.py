"""
FHIR ClinicalImpression document -> search index. The only write-side mapper.

ClinicalImpression's whole resource is stored verbatim in ClinicalImpressionModel.content; this
module derives every *other* column and child row from it — exactly the values the FHIR R4
ClinicalImpression search parameters filter on
(https://www.hl7.org/fhir/R4/clinicalimpression.html#search), nothing more. See
ClinicalImpressionModel's docstring for the parameter -> storage table; the shared builders are
in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.clinical_impression import (
    ASSESSOR_TYPES,
    FINDING_TYPES,
    INVESTIGATION_TYPES,
    PROBLEM_TYPES,
    SUBJECT_TYPES,
    ClinicalImpressionIdentifier,
    ClinicalImpressionReference,
    ClinicalImpressionStatus,
    ClinicalImpressionToken,
)
from app.repository._content_index import identifier_rows, period_bounds, relative, type_rows

from ._shared import any_typed, typed

# Of the investigation targets, these are resources here (Observation, Media, ImagingStudy and
# QuestionnaireResponse are not rebuilt yet).
_MODELED_INVESTIGATIONS = ("RiskAssessment", "FamilyMemberHistory", "DiagnosticReport")
# Of the finding.itemReference targets, only Condition is a resource here.
_MODELED_FINDINGS = ("Condition",)
# Reference(Any) `supportingInfo` targets that are existence-checked on write: the resources
# already rebuilt that supporting information can be.
_MODELED_INFORMATION = (
    "Patient", "Practitioner", "PractitionerRole", "RelatedPerson", "Organization", "Location", "Encounter",
    "Appointment", "Condition", "Procedure", "DiagnosticReport", "AllergyIntolerance", "Immunization",
    "FamilyMemberHistory", "RiskAssessment", "ClinicalImpression",
)
_AUTHOR_TYPES = ("Practitioner", "PractitionerRole", "Patient", "RelatedPerson", "Organization")
_STATUSES = {m.value for m in ClinicalImpressionStatus}


def local_references(document: dict) -> list[tuple[str, str, str]]:
    """(element label, resource type, relative reference) for every local
    reference that must exist in the caller's org on write: identifier.assigner, `subject`
    (a Patient), `encounter`, `assessor`, `previous`, every `problem`, every
    `investigation.item` that is a RiskAssessment, FamilyMemberHistory or DiagnosticReport,
    every `finding.itemReference` that is a Condition, every `prognosisReference`, every
    `supportingInfo` that is a rebuilt resource and every note's `authorReference`. Absolute
    URLs, logical (identifier-only) references and targets that are not resources on this
    server (a Group subject, an Observation / Media / ImagingStudy / QuestionnaireResponse
    investigation, an Observation / Media finding) point elsewhere and are not checked."""
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
        add("identifier.assigner", (identifier.get("assigner") or {}).get("reference"), "Organization")
    add("subject", (document.get("subject") or {}).get("reference"), "Patient")
    add("encounter", (document.get("encounter") or {}).get("reference"), "Encounter")
    add_typed("assessor", document.get("assessor"), ASSESSOR_TYPES)
    add("previous", (document.get("previous") or {}).get("reference"), "ClinicalImpression")
    for ref in document.get("problem") or []:
        add_typed("problem", ref, PROBLEM_TYPES)
    for investigation in document.get("investigation") or []:
        for ref in (investigation or {}).get("item") or []:
            add_typed("investigation.item", ref, _MODELED_INVESTIGATIONS)
    for finding in document.get("finding") or []:
        add_typed("finding.itemReference", (finding or {}).get("itemReference"), _MODELED_FINDINGS)
    for ref in document.get("prognosisReference") or []:
        add("prognosisReference", (ref or {}).get("reference"), "RiskAssessment")
    for ref in document.get("supportingInfo") or []:
        add_typed("supportingInfo", ref, _MODELED_INFORMATION)
    for note in document.get("note") or []:
        add_typed("note.authorReference", (note or {}).get("authorReference"), _AUTHOR_TYPES)
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
    """Search columns on the clinical_impression row itself."""
    value = document.get("date")
    start, end = period_bounds({"start": value, "end": value}) if value else (None, None)
    status = document.get("status")
    return {
        "status": ClinicalImpressionStatus(status) if status in _STATUSES else None,
        "date_start": start,
        "date_end": end,
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("encounter", document.get("encounter"), ("Encounter",)),
        **_ref_columns("assessor", document.get("assessor"), ASSESSOR_TYPES),
        **_ref_columns("previous", document.get("previous"), ("ClinicalImpression",)),
    }


def _token_rows(document: dict) -> list:
    rows = []
    for finding in document.get("finding") or []:
        concept = (finding or {}).get("itemCodeableConcept")
        if concept:
            rows += type_rows(partial(ClinicalImpressionToken, param="finding-code"), concept)
    return rows


def _reference_row(param: str, ref: dict | None, allowed: tuple[str, ...] | None) -> ClinicalImpressionReference | None:
    """One index row for a Reference with a `reference` or an `identifier`
    (display-only cannot be matched by a reference search). `allowed` None means
    Reference(Any): any relative `Type/<id>` names a type."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = any_typed(reference) if allowed is None else typed(reference, allowed)
    return ClinicalImpressionReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    rows = [_reference_row("problem", r, PROBLEM_TYPES) for r in document.get("problem") or []]
    for investigation in document.get("investigation") or []:
        rows += [_reference_row("investigation", r, INVESTIGATION_TYPES) for r in (investigation or {}).get("item") or []]
    for finding in document.get("finding") or []:
        rows.append(_reference_row("finding-ref", (finding or {}).get("itemReference"), FINDING_TYPES))
    rows += [_reference_row("supporting-info", r, None) for r in document.get("supportingInfo") or []]
    return [r for r in rows if r]


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by ClinicalImpressionModel relationship name."""
    return {
        "identifiers": [
            r for i in document.get("identifier") or [] for r in identifier_rows(ClinicalImpressionIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
    }
