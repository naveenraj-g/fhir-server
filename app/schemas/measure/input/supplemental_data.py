from pydantic import BaseModel, ConfigDict, Field

from app.schemas.measure.input.codeable_concept import MeasureCodeableConceptInput
from app.schemas.measure.input.group import MeasureExpressionInput


class MeasureSupplementalDataInput(BaseModel):
    """Measure.supplementalData input schema."""

    model_config = ConfigDict(extra="forbid")

    code: MeasureCodeableConceptInput | None = Field(None, description="Meaning of the supplemental data.")
    usage: list[MeasureCodeableConceptInput] | None = Field(
        None, description="supplemental-data | risk-adjustment-factor."
    )
    description: str | None = Field(None, description="The human readable description of this supplemental data.")
    criteria: MeasureExpressionInput = Field(..., description="The criteria that defines the supplemental data (1..1 Expression).")
