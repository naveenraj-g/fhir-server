from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRObservationDefinitionSchema(BaseModel):
    resourceType: str = Field(
        "ObservationDefinition", description="Always 'ObservationDefinition'."
    )
    id: str = Field(..., description="Public observation_definition_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Business identifier for this ObservationDefinition instance."
    )
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="Category of observation."
    )
    code: FHIRCodeableConcept | None = Field(
        None, description="Type of observation (code / type)."
    )
    permittedDataType: list[str] | None = Field(
        None,
        description="Quantity | CodeableConcept | string | boolean | integer | Range | Ratio | SampledData | time | dateTime | Period.",
    )
    multipleResultsAllowed: bool | None = Field(
        None, description="Multiple results allowed."
    )
    method: FHIRCodeableConcept | None = Field(
        None, description="Method used to produce the observation."
    )
    preferredReportName: str | None = Field(None, description="Preferred report name.")
    quantitativeDetails: dict | None = Field(
        None, description="Characteristics of quantitative results."
    )
    qualifiedInterval: list[dict] | None = Field(
        None,
        description="Qualified range for continuous and ordinal observation results.",
    )
    validCodedValueSet: FHIRReference | None = Field(
        None, description="Value set of valid coded values."
    )
    normalCodedValueSet: FHIRReference | None = Field(
        None, description="Value set of normal coded values."
    )
    abnormalCodedValueSet: FHIRReference | None = Field(
        None, description="Value set of abnormal coded values."
    )
    criticalCodedValueSet: FHIRReference | None = Field(
        None, description="Value set of critical coded values."
    )


class FHIRObservationDefinitionBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRObservationDefinitionSchema | dict = Field(
        ...,
        description="An ObservationDefinition (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED) or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRObservationDefinitionBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages. Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRObservationDefinitionBundleEntry] | None = None
