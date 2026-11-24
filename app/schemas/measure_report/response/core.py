from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRMeasureReportSchema(BaseModel):
    resourceType: str = Field("MeasureReport", description="Always 'MeasureReport'.")
    id: str = Field(..., description="Public measure_report_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Additional identifier."
    )
    status: str | None = Field(None, description="complete | pending | error.")
    type: str | None = Field(
        None, description="individual | subject-list | summary | data-collection."
    )
    measure: str | None = Field(
        None,
        description="What measure was calculated (the canonical URL of a Measure).",
    )
    subject: FHIRReference | None = Field(
        None, description="What individual(s) the report is for."
    )
    date: str | None = Field(None, description="When the report was generated.")
    reporter: FHIRReference | None = Field(
        None, description="Who is reporting the data."
    )
    period: FHIRPeriod | None = Field(
        None, description="What period the report covers."
    )
    improvementNotation: FHIRCodeableConcept | None = Field(
        None, description="increase | decrease."
    )
    group: list[dict] | None = Field(
        None, description="Measure results for each group."
    )
    evaluatedResource: list[FHIRReference] | None = Field(
        None, description="What data was used to calculate the measure score."
    )


class FHIRMeasureReportBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRMeasureReportSchema | dict = Field(
        ...,
        description="A MeasureReport (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRMeasureReportBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRMeasureReportBundleEntry] | None = None
