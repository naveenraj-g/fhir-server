from pydantic import BaseModel, ConfigDict, Field

from .codeable_concept import ObservationDefinitionCodeableConceptInput


class ObservationDefinitionQuantitativeDetailsInput(BaseModel):
    """ObservationDefinition.quantitativeDetails (0..1) input schema."""

    model_config = ConfigDict(extra="forbid")

    customary_unit: ObservationDefinitionCodeableConceptInput | None = Field(
        None, description="Customary unit used to report quantitative results."
    )
    unit: ObservationDefinitionCodeableConceptInput | None = Field(
        None, description="SI unit used to report quantitative results."
    )
    conversion_factor: float | None = Field(
        None, description="Factor for converting value expressed with SI unit to customary unit."
    )
    decimal_precision: int | None = Field(
        None, description="Number of digits after decimal separator."
    )
