from pydantic import BaseModel, ConfigDict, Field

from app.schemas.medication_statement.input.codeable_concept import MedicationStatementCodingInput


class MedicationStatementReasonCodeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str | None = Field(None, description="Plain text representation of the reason concept.")
    coding: list[MedicationStatementCodingInput] | None = Field(
        None, description="Codes defined by a terminology system."
    )
