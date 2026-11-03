from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRCodeableConcept, FHIRReference
from app.schemas.medication.response.codeable_concept import (
    PlainMedicationCodeableConcept,
)
from app.schemas.medication.response.quantity import (
    FHIRRatio,
    PlainMedicationRatio,
)
from app.schemas.medication.response.reference import (
    PlainMedicationReference,
)


class FHIRMedicationIngredient(BaseModel):
    """Medication.ingredient (0..* BackboneElement) in FHIR R4."""

    model_config = ConfigDict(extra="allow")

    itemCodeableConcept: FHIRCodeableConcept | None = Field(None, description="The business code that represents the active or inactive ingredient.")
    itemReference: FHIRReference | None = Field(None, description="The actual ingredient (Reference(Substance | Medication)).")
    isActive: bool | None = Field(None, description="Active ingredient indicator.")
    strength: FHIRRatio | None = Field(None, description="Quantity of ingredient present.")


class PlainMedicationIngredient(BaseModel):
    """Medication.ingredient in plain snake_case."""

    model_config = ConfigDict(extra="allow")

    id: int
    item_codeable_concept: PlainMedicationCodeableConcept | None = None
    item_reference: PlainMedicationReference | None = None
    is_active: bool | None = None
    strength: PlainMedicationRatio | None = None
