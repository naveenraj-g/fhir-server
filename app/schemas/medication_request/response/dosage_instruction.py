from pydantic import BaseModel, ConfigDict, Field

from .codeable_concept import PlainMedicationRequestCode, PlainMedicationRequestCodeableConcept


class PlainMedicationRequestDosageInstruction(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal row ID.")
    sequence: int | None = Field(None, description="The order of the dosage instructions.")
    text: str | None = Field(None, description="Free text dosage instructions.")
    additional_instruction: list[PlainMedicationRequestCodeableConcept] | None = Field(None, description="Supplemental instructions/warnings.")
    patient_instruction: str | None = Field(None, description="Patient/consumer-oriented instructions.")
    timing: dict | None = Field(None, description="Raw FHIR Timing dict.")
    as_needed_boolean: bool | None = Field(None, description="asNeeded[x]: boolean.")
    as_needed_codeable_concept: PlainMedicationRequestCode | None = Field(None, description="asNeeded[x]: CodeableConcept.")
    site: PlainMedicationRequestCode | None = Field(None, description="Body site to administer to.")
    route: PlainMedicationRequestCode | None = Field(None, description="How the drug should enter the body.")
    method: PlainMedicationRequestCode | None = Field(None, description="Technique for administering the medication.")
    dose_and_rate: list[dict] | None = Field(None, description="Raw FHIR dose[x]/rate[x] dicts.")
    max_dose_per_period: dict | None = Field(None, description="Raw FHIR Ratio dict.")
    max_dose_per_administration_value: float | None = Field(None, description="Upper limit per administration — numeric value.")
    max_dose_per_administration_unit: str | None = Field(None, description="Upper limit per administration — unit.")
    max_dose_per_administration_system: str | None = Field(None, description="Upper limit per administration — unit system.")
    max_dose_per_administration_code: str | None = Field(None, description="Upper limit per administration — coded unit form.")
    max_dose_per_lifetime_value: float | None = Field(None, description="Upper limit per lifetime — numeric value.")
    max_dose_per_lifetime_unit: str | None = Field(None, description="Upper limit per lifetime — unit.")
    max_dose_per_lifetime_system: str | None = Field(None, description="Upper limit per lifetime — unit system.")
    max_dose_per_lifetime_code: str | None = Field(None, description="Upper limit per lifetime — coded unit form.")
