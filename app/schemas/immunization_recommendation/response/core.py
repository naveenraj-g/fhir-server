from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)
from app.schemas.immunization_recommendation.response.identifier import (
    PlainImmunizationRecommendationIdentifier,
)
from app.schemas.immunization_recommendation.response.recommendation import (
    FHIRImmunizationRecommendationRecommendation,
    PlainImmunizationRecommendationRecommendation,
)
from app.schemas.immunization_recommendation.response.reference import (
    PlainImmunizationRecommendationReference,
)


class FHIRImmunizationRecommendationSchema(BaseModel):
    """FHIR R4 ImmunizationRecommendation resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["ImmunizationRecommendation"] = "ImmunizationRecommendation"
    id: str = Field(..., description="Logical id of this artifact.")
    meta: FHIRMeta | None = Field(None, description="Metadata about the resource.")
    extension: list[dict] | None = Field(None, description="Additional content defined by implementations.")
    identifier: list[FHIRIdentifier] | None = Field(None, description="Business identifier.")
    patient: FHIRReference = Field(..., description="Who this profile is for.")
    date: str = Field(..., description="Date the recommendation(s) were generated.")
    authority: FHIRReference | None = Field(None, description="Who is responsible for protocol.")
    recommendation: list[FHIRImmunizationRecommendationRecommendation] = Field(
        ..., description="Vaccine administration recommendations."
    )


class PlainImmunizationRecommendationResponse(BaseModel):
    """Plain snake_case ImmunizationRecommendation response."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Public numeric ID (starts at 510000).")
    identifier: list[PlainImmunizationRecommendationIdentifier] | None = Field(
        None, description="Business identifier."
    )
    patient: PlainImmunizationRecommendationReference = Field(
        ..., description="Who this profile is for."
    )
    date: datetime = Field(..., description="Date the recommendation(s) were generated.")
    authority: PlainImmunizationRecommendationReference | None = Field(
        None, description="Who is responsible for protocol."
    )
    recommendation: list[PlainImmunizationRecommendationRecommendation] = Field(
        ..., description="Vaccine administration recommendations."
    )

    # Audit fields
    tenant_id: str | None = Field(None, description="Tenant organization ID.")
    created_by: str | None = Field(None, description="User who created the record.")
    updated_by: str | None = Field(None, description="User who last updated the record.")
    created_at: datetime | None = Field(None, description="Record creation timestamp.")
    updated_at: datetime | None = Field(None, description="Record update timestamp.")


class FHIRImmunizationRecommendationBundleEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    fullUrl: str = Field(..., description="Full URL of the resource.")
    resource: FHIRImmunizationRecommendationSchema = Field(
        ..., description="The ImmunizationRecommendation resource."
    )


class FHIRImmunizationRecommendationBundle(BaseModel):
    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Bundle"] = "Bundle"
    type: str = "searchset"
    total: int = Field(..., description="Total number of matches.")
    entry: list[FHIRImmunizationRecommendationBundleEntry] = Field(
        default_factory=list, description="Entry in the bundle."
    )


class PaginatedImmunizationRecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(..., description="Total number of records matching the query.")
    limit: int = Field(..., description="Maximum number of records returned.")
    offset: int = Field(..., description="Offset of the first record returned.")
    data: list[PlainImmunizationRecommendationResponse] = Field(
        ..., description="List of immunization recommendation records."
    )
