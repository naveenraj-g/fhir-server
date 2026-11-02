from pydantic import BaseModel, ConfigDict, Field

from .codeable_concept import ClinicalImpressionCodeableConceptInput
from .reference import ClinicalImpressionInvestigationItemInput


class ClinicalImpressionInvestigationInput(BaseModel):
    """ClinicalImpression.investigation (0..* BackboneElement) input."""

    model_config = ConfigDict(extra="forbid")

    code: ClinicalImpressionCodeableConceptInput = Field(
        ..., description="A name/code for the set of investigations conducted."
    )
    item: list[ClinicalImpressionInvestigationItemInput] | None = Field(
        None, description="Record of a specific investigation was performed."
    )
