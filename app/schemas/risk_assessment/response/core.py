from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRRange,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRRiskAssessmentAnnotation(BaseModel):
    authorReference: FHIRReference | None = Field(
        None, description="Individual responsible for the annotation."
    )
    authorString: str | None = Field(
        None, description="Individual responsible for the annotation, as plain text."
    )
    time: str | None = Field(None, description="When the annotation was made.")
    text: str | None = Field(None, description="The annotation text.")


class FHIRRiskAssessmentPrediction(BaseModel):
    outcome: FHIRCodeableConcept | None = Field(
        None, description="Possible outcome for the subject."
    )
    probabilityDecimal: float | None = Field(
        None, description="Likelihood of specified outcome (decimal)."
    )
    probabilityRange: FHIRRange | None = Field(
        None, description="Likelihood of specified outcome (Range)."
    )
    qualitativeRisk: FHIRCodeableConcept | None = Field(
        None, description="Likelihood of specified outcome as a qualitative value."
    )
    relativeRisk: float | None = Field(None, description="Relative likelihood.")
    whenPeriod: FHIRPeriod | None = Field(
        None, description="Timeframe or age range (Period)."
    )
    whenRange: FHIRRange | None = Field(
        None, description="Timeframe or age range (Range)."
    )
    rationale: str | None = Field(None, description="Explanation of prediction.")


class FHIRRiskAssessmentSchema(BaseModel):
    resourceType: str = Field("RiskAssessment", description="Always 'RiskAssessment'.")
    id: str = Field(..., description="Public risk_assessment_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Unique identifier for the assessment."
    )
    basedOn: FHIRReference | None = Field(
        None, description="Request fulfilled by this assessment."
    )
    parent: FHIRReference | None = Field(None, description="Part of this occurrence.")
    status: str | None = Field(
        None,
        description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown.",
    )
    method: FHIRCodeableConcept | None = Field(
        None, description="Evaluation mechanism."
    )
    code: FHIRCodeableConcept | None = Field(None, description="Type of assessment.")
    subject: FHIRReference | None = Field(
        None, description="Who/what does assessment apply to."
    )
    encounter: FHIRReference | None = Field(
        None, description="Where was assessment performed?"
    )
    occurrenceDateTime: str | None = Field(
        None, description="When was assessment made? (dateTime)."
    )
    occurrencePeriod: FHIRPeriod | None = Field(
        None, description="When was assessment made? (Period)."
    )
    condition: FHIRReference | None = Field(None, description="Condition assessed.")
    performer: FHIRReference | None = Field(None, description="Who did assessment?")
    reasonCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Why the assessment was necessary?"
    )
    reasonReference: list[FHIRReference] | None = Field(
        None, description="Why the assessment was necessary?"
    )
    basis: list[FHIRReference] | None = Field(
        None, description="Information used in assessment."
    )
    prediction: list[FHIRRiskAssessmentPrediction] | None = Field(
        None, description="Outcome predicted."
    )
    mitigation: str | None = Field(None, description="How to reduce risk.")
    note: list[FHIRRiskAssessmentAnnotation] | None = Field(
        None, description="Comments on the risk assessment."
    )


class FHIRRiskAssessmentBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRRiskAssessmentSchema | dict = Field(
        ...,
        description="A RiskAssessment (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Encounter / Condition / Practitioner / PractitionerRole (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRRiskAssessmentBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRRiskAssessmentBundleEntry] | None = None
