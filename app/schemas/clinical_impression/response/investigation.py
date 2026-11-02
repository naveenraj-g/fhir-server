from pydantic import BaseModel, ConfigDict, Field

from .codeable_concept import PlainClinicalImpressionCodeableConcept
from .reference import PlainClinicalImpressionReference


class PlainClinicalImpressionInvestigation(BaseModel):
    """Plain snake_case representation for ClinicalImpression.investigation."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Internal DB ID.")
    code: PlainClinicalImpressionCodeableConcept = Field(
        ..., description="A name/code for the set of investigations conducted."
    )
    item: list[PlainClinicalImpressionReference] | None = Field(
        None, description="Record of a specific investigation performed."
    )


class ClinicalImpressionInvestigationListItem(PlainClinicalImpressionInvestigation):
    """Sub-resource list item for investigation."""


class ClinicalImpressionInvestigationListResponse(BaseModel):
    """Sub-resource list response for investigations."""

    model_config = ConfigDict(extra="forbid")

    data: list[ClinicalImpressionInvestigationListItem] = Field(..., description="List of investigations.")
    total: int = Field(..., description="Total count.")
