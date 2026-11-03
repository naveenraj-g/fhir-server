from pydantic import BaseModel, ConfigDict, Field

from app.schemas.medication_dispense.input.codeable_concept import (
    MedicationDispenseCodeableConceptInput,
)
from app.schemas.medication_dispense.input.reference import (
    MedicationDispenseSubstitutionResponsiblePartyInput,
)


class MedicationDispenseSubstitutionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    was_substituted: bool = Field(..., description="Whether a substitution was or was not performed on the dispense.")
    type: MedicationDispenseCodeableConceptInput | None = Field(None, description="Code signifying whether a different drug was dispensed from what was prescribed.")
    reason: list[MedicationDispenseCodeableConceptInput] | None = Field(None, description="Why was substitution made.")
    responsible_party: list[MedicationDispenseSubstitutionResponsiblePartyInput] | None = Field(
        None, description="Who is responsible for the substitution."
    )
