from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRImmunizationEvaluationSchema(BaseModel):
    resourceType: str = Field(
        "ImmunizationEvaluation", description="Always 'ImmunizationEvaluation'."
    )
    id: str = Field(..., description="Public immunization_evaluation_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Business identifier."
    )
    status: str | None = Field(None, description="completed | entered-in-error.")
    patient: FHIRReference | None = Field(
        None, description="Who this evaluation is for."
    )
    date: str | None = Field(None, description="Date the evaluation was performed.")
    authority: FHIRReference | None = Field(
        None, description="Who is responsible for publishing the recommendations."
    )
    targetDisease: FHIRCodeableConcept | None = Field(
        None, description="Evaluation target disease."
    )
    immunizationEvent: FHIRReference | None = Field(
        None, description="Immunization being evaluated."
    )
    doseStatus: FHIRCodeableConcept | None = Field(
        None, description="Status of the dose relative to published recommendations."
    )
    doseStatusReason: list[FHIRCodeableConcept] | None = Field(
        None, description="Reason for the dose status."
    )
    description: str | None = Field(None, description="Evaluation notes.")
    series: str | None = Field(None, description="Name of the vaccine series.")
    doseNumberPositiveInt: int | None = Field(
        None, description="Dose number within the series."
    )
    doseNumberString: str | None = Field(
        None, description="Dose number within the series (string)."
    )
    seriesDosesPositiveInt: int | None = Field(
        None, description="Recommended number of doses for immunity."
    )
    seriesDosesString: str | None = Field(
        None, description="Recommended number of doses for immunity (string)."
    )


class FHIRImmunizationEvaluationBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRImmunizationEvaluationSchema | dict = Field(
        ...,
        description="An ImmunizationEvaluation (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Immunization (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRImmunizationEvaluationBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRImmunizationEvaluationBundleEntry] | None = None
