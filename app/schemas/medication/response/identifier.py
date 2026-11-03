from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.medication.response.codeable_concept import (
    PlainMedicationCodeableConcept,
)
from app.schemas.medication.response.reference import (
    PlainMedicationReference,
)


class PlainMedicationIdentifier(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    use: str | None = None
    type: PlainMedicationCodeableConcept | None = None
    system: str | None = None
    value: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    assigner: PlainMedicationReference | None = None
