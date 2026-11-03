from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRCodeableConcept, FHIRQuantity
from app.schemas.medication_dispense.response.codeable_concept import (
    PlainMedicationDispenseCodeableConcept,
)


class FHIRMedicationDispenseDosage(BaseModel):
    model_config = ConfigDict(extra="allow")

    sequence: int | None = None
    text: str | None = None
    additionalInstruction: list[FHIRCodeableConcept] | None = None
    patientInstruction: str | None = None
    timing: dict | None = None
    asNeededBoolean: bool | None = None
    asNeededCodeableConcept: FHIRCodeableConcept | None = None
    site: FHIRCodeableConcept | None = None
    route: FHIRCodeableConcept | None = None
    method: FHIRCodeableConcept | None = None
    doseAndRate: list[dict] | None = None
    maxDosePerPeriod: dict | None = None
    maxDosePerAdministration: FHIRQuantity | None = None
    maxDosePerLifetime: FHIRQuantity | None = None


class PlainMedicationDispenseDosage(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal DB ID.")
    sequence: int | None = None
    text: str | None = None
    additional_instruction: list[PlainMedicationDispenseCodeableConcept] | None = None
    patient_instruction: str | None = None
    timing: dict | None = None
    as_needed_boolean: bool | None = None
    as_needed_codeable_concept: PlainMedicationDispenseCodeableConcept | None = None
    site: PlainMedicationDispenseCodeableConcept | None = None
    route: PlainMedicationDispenseCodeableConcept | None = None
    method: PlainMedicationDispenseCodeableConcept | None = None
    dose_and_rate: list[dict] | None = None
    max_dose_per_period: dict | None = None
    max_dose_per_administration_value: float | None = None
    max_dose_per_administration_unit: str | None = None
    max_dose_per_administration_system: str | None = None
    max_dose_per_administration_code: str | None = None
    max_dose_per_lifetime_value: float | None = None
    max_dose_per_lifetime_unit: str | None = None
    max_dose_per_lifetime_system: str | None = None
    max_dose_per_lifetime_code: str | None = None
