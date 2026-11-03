from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import AuditFields
from app.schemas.enums import IdentifierUse
from app.schemas.medication_dispense.response.codeable_concept import (
    PlainMedicationDispenseCodeableConcept,
)
from app.schemas.medication_dispense.response.reference import (
    PlainMedicationDispenseReference,
)


class PlainMedicationDispenseIdentifier(AuditFields, BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal DB ID.")
    use: IdentifierUse | None = None
    type: PlainMedicationDispenseCodeableConcept | None = None
    system: str | None = None
    value: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    assigner: PlainMedicationDispenseReference | None = None
