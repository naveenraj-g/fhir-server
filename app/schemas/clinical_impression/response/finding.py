from pydantic import BaseModel, ConfigDict, Field

from .codeable_concept import PlainClinicalImpressionCodeableConcept
from .reference import PlainClinicalImpressionReference


class PlainClinicalImpressionFinding(BaseModel):
    """Plain snake_case representation for ClinicalImpression.finding."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Internal DB ID.")
    item_codeable_concept: PlainClinicalImpressionCodeableConcept | None = Field(
        None, description="What was found (codeable concept)."
    )
    item_reference: PlainClinicalImpressionReference | None = Field(
        None, description="What was found (reference to Condition, Observation, Media)."
    )
    basis: str | None = Field(
        None, description="Which investigations support finding."
    )


class ClinicalImpressionFindingListItem(PlainClinicalImpressionFinding):
    """Sub-resource list item for finding."""


class ClinicalImpressionFindingListResponse(BaseModel):
    """Sub-resource list response for findings."""

    model_config = ConfigDict(extra="forbid")

    data: list[ClinicalImpressionFindingListItem] = Field(..., description="List of findings.")
    total: int = Field(..., description="Total count.")
