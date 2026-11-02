from pydantic import BaseModel, ConfigDict

from app.schemas.medication_statement.response.codeable_concept import (
    PlainMedicationStatementCode,
)


class PlainMedicationStatementReasonCode(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    text: str | None = None
    coding: list[PlainMedicationStatementCode] | None = None
