from pydantic import BaseModel, ConfigDict, Field

from app.schemas.activity_definition.input.codeable_concept import (
    ActivityDefinitionCodeableConceptInput,
)


class ActivityDefinitionDosageInput(BaseModel):
    """ActivityDefinition.dosage (0..* Dosage) input schema."""

    model_config = ConfigDict(extra="forbid")

    sequence: int | None = Field(None, description="Order of dosage instruction.")
    text: str | None = Field(None, description="Free text dosage instructions.")
    patient_instruction: str | None = Field(None, description="Patient-oriented instructions.")
    timing: dict | None = Field(None, description="When medication should be administered.")
    as_needed_boolean: bool | None = Field(None, description="Take 'as needed' (boolean).")
    as_needed_codeable_concept: ActivityDefinitionCodeableConceptInput | None = Field(
        None, description="Take 'as needed' (CodeableConcept)."
    )
    site: ActivityDefinitionCodeableConceptInput | None = Field(None, description="Body site to administer to.")
    route: ActivityDefinitionCodeableConceptInput | None = Field(None, description="How drug should enter body.")
    method: ActivityDefinitionCodeableConceptInput | None = Field(None, description="Technique for administering medication.")
    dose_and_rate: list[dict] | None = Field(None, description="Amount of medication administered.")
    max_dose_per_period: dict | None = Field(None, description="Upper limit on medication per unit of time (Ratio).")
    max_dose_per_administration_value: float | None = Field(None, description="Upper limit on medication per administration value.")
    max_dose_per_administration_unit: str | None = Field(None, description="Upper limit on medication per administration unit.")
    max_dose_per_administration_system: str | None = Field(None, description="Upper limit on medication per administration system.")
    max_dose_per_administration_code: str | None = Field(None, description="Upper limit on medication per administration code.")
    max_dose_per_lifetime_value: float | None = Field(None, description="Upper limit on medication per lifetime of the patient value.")
    max_dose_per_lifetime_unit: str | None = Field(None, description="Upper limit on medication per lifetime unit.")
    max_dose_per_lifetime_system: str | None = Field(None, description="Upper limit on medication per lifetime system.")
    max_dose_per_lifetime_code: str | None = Field(None, description="Upper limit on medication per lifetime code.")
