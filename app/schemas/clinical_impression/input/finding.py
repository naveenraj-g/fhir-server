from pydantic import BaseModel, ConfigDict, Field

from .codeable_concept import ClinicalImpressionCodeableConceptInput
from .reference import ClinicalImpressionFindingReferenceInput


class ClinicalImpressionFindingInput(BaseModel):
    """ClinicalImpression.finding (0..* BackboneElement) input."""

    model_config = ConfigDict(extra="forbid")

    item_codeable_concept: ClinicalImpressionCodeableConceptInput | None = Field(
        None, description="What was found (codeable concept)."
    )
    item_reference: ClinicalImpressionFindingReferenceInput | None = Field(
        None, description="What was found (reference to Condition, Observation, Media)."
    )
    basis: str | None = Field(
        None, description="Which investigations support finding."
    )
