from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRCodeableConcept, FHIRQuantity
from app.schemas.medication_administration.response.codeable_concept import (
    PlainMedicationAdministrationCodeableConcept,
)


class FHIRRatio(BaseModel):
    model_config = ConfigDict(extra="allow")

    numerator: FHIRQuantity | None = None
    denominator: FHIRQuantity | None = None


class FHIRMedicationAdministrationDosage(BaseModel):
    model_config = ConfigDict(extra="allow")

    text: str | None = Field(None, description="Free text dosage instructions.")
    site: FHIRCodeableConcept | None = Field(None, description="Body site administered to.")
    route: FHIRCodeableConcept | None = Field(None, description="Path of substance into body.")
    method: FHIRCodeableConcept | None = Field(None, description="How drug was administered.")
    dose: FHIRQuantity | None = Field(None, description="Amount of medication per dose.")
    rateRatio: FHIRRatio | None = Field(None, description="Dose quantity per unit of time (Ratio).")
    rateQuantity: FHIRQuantity | None = Field(None, description="Dose quantity per unit of time (Quantity).")


class PlainQuantity(BaseModel):
    model_config = ConfigDict(extra="allow")

    value: float | None = None
    unit: str | None = None
    system: str | None = None
    code: str | None = None


class PlainRatio(BaseModel):
    model_config = ConfigDict(extra="allow")

    numerator: PlainQuantity | None = None
    denominator: PlainQuantity | None = None


class PlainMedicationAdministrationDosage(BaseModel):
    model_config = ConfigDict(extra="allow")

    text: str | None = None
    site: PlainMedicationAdministrationCodeableConcept | None = None
    route: PlainMedicationAdministrationCodeableConcept | None = None
    method: PlainMedicationAdministrationCodeableConcept | None = None
    dose: PlainQuantity | None = None
    rate_ratio: PlainRatio | None = None
    rate_quantity: PlainQuantity | None = None
