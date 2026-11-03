from pydantic import BaseModel, ConfigDict, Field

from app.schemas.medication_administration.input.codeable_concept import (
    MedicationAdministrationCodeableConceptInput,
)
from app.schemas.medication_administration.input.quantity import (
    RatioInput,
    SimpleQuantityInput,
)


class MedicationAdministrationDosageInput(BaseModel):
    """MedicationAdministration.dosage (0..1 BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    text: str | None = Field(None, description="Free text dosage instructions.")
    site: MedicationAdministrationCodeableConceptInput | None = Field(
        None, description="Body site administered to."
    )
    route: MedicationAdministrationCodeableConceptInput | None = Field(
        None, description="Path of substance into body."
    )
    method: MedicationAdministrationCodeableConceptInput | None = Field(
        None, description="How drug was administered."
    )
    dose: SimpleQuantityInput | None = Field(
        None, description="Amount of medication per dose."
    )
    rate_ratio: RatioInput | None = Field(
        None, description="Dose quantity per unit of time (Ratio)."
    )
    rate_quantity: SimpleQuantityInput | None = Field(
        None, description="Dose quantity per unit of time (Quantity)."
    )
