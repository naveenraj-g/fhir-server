from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRReference,
)
from app.schemas.medication_dispense.response.codeable_concept import (
    PlainMedicationDispenseCodeableConcept,
)
from app.schemas.medication_dispense.response.reference import (
    PlainMedicationDispenseReference,
)


class FHIRMedicationDispenseSubstitution(BaseModel):
    model_config = ConfigDict(extra="allow")

    wasSubstituted: bool = Field(..., description="Whether a substitution was or was not performed.")
    type: FHIRCodeableConcept | None = Field(None, description="Code signifying whether a different drug was dispensed.")
    reason: list[FHIRCodeableConcept] | None = Field(None, description="Why was substitution made.")
    responsibleParty: list[FHIRReference] | None = Field(None, description="Who is responsible for the substitution.")


class PlainMedicationDispenseSubstitution(BaseModel):
    model_config = ConfigDict(extra="allow")

    was_substituted: bool | None = None
    type: PlainMedicationDispenseCodeableConcept | None = None
    reason: list[PlainMedicationDispenseCodeableConcept] | None = None
    responsible_party: list[PlainMedicationDispenseReference] | None = None
