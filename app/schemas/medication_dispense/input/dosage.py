from pydantic import BaseModel, ConfigDict, Field

from app.schemas.medication_dispense.input.codeable_concept import (
    MedicationDispenseCodeableConceptInput,
)


class MedicationDispenseDosageInstructionInput(BaseModel):
    """MedicationDispense.dosageInstruction (0..* Dosage) —
    https://www.hl7.org/fhir/R4/datatypes.html#Dosage
    """

    model_config = ConfigDict(extra="forbid")

    sequence: int | None = Field(None, description="The order of the dosage instructions.")
    text: str | None = Field(None, description="Free text dosage instructions.")
    additional_instruction: list[MedicationDispenseCodeableConceptInput] | None = Field(
        None, description="Supplemental instructions or warnings to the patient."
    )
    patient_instruction: str | None = Field(None, description="Patient/consumer-oriented instructions.")
    timing: dict | None = Field(None, description="When medication should be administered, as a raw FHIR Timing dict.")
    as_needed_boolean: bool | None = Field(None, description="asNeeded[x]: boolean.")
    as_needed_codeable_concept: MedicationDispenseCodeableConceptInput | None = Field(
        None, description="asNeeded[x]: CodeableConcept."
    )
    site: MedicationDispenseCodeableConceptInput | None = Field(None, description="Body site to administer to.")
    route: MedicationDispenseCodeableConceptInput | None = Field(None, description="How the drug should enter the body.")
    method: MedicationDispenseCodeableConceptInput | None = Field(None, description="Technique for administering the medication.")
    dose_and_rate: list[dict] | None = Field(
        None, description="Amount of medication administered, as raw FHIR dose[x]/rate[x] dicts."
    )
    max_dose_per_period: dict | None = Field(None, description="Upper limit on medication per unit of time, as a raw FHIR Ratio dict.")
    max_dose_per_administration_value: float | None = Field(None, description="Upper limit on medication per administration — numeric value.")
    max_dose_per_administration_unit: str | None = Field(None, description="Upper limit on medication per administration — unit.")
    max_dose_per_administration_system: str | None = Field(None, description="Upper limit on medication per administration — unit system.")
    max_dose_per_administration_code: str | None = Field(None, description="Upper limit on medication per administration — coded unit form.")
    max_dose_per_lifetime_value: float | None = Field(None, description="Upper limit on medication per lifetime of the patient — numeric value.")
    max_dose_per_lifetime_unit: str | None = Field(None, description="Upper limit on medication per lifetime — unit.")
    max_dose_per_lifetime_system: str | None = Field(None, description="Upper limit on medication per lifetime — unit system.")
    max_dose_per_lifetime_code: str | None = Field(None, description="Upper limit on medication per lifetime — coded unit form.")
