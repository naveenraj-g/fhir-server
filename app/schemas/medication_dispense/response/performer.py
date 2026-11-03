from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    AuditFields,
    FHIRCodeableConcept,
    FHIRReference,
)
from app.schemas.medication_dispense.response.codeable_concept import (
    PlainMedicationDispenseCodeableConcept,
)
from app.schemas.medication_dispense.response.reference import (
    PlainMedicationDispenseReference,
)


class FHIRMedicationDispensePerformer(BaseModel):
    model_config = ConfigDict(extra="allow")

    function: FHIRCodeableConcept | None = Field(None, description="Who performed.")
    actor: FHIRReference = Field(..., description="Individual who was performing.")


class PlainMedicationDispensePerformer(AuditFields, BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal DB ID.")
    function: PlainMedicationDispenseCodeableConcept | None = None
    actor: PlainMedicationDispenseReference
