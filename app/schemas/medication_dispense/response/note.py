from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import AuditFields, FHIRReference
from app.schemas.medication_dispense.response.reference import (
    PlainMedicationDispenseReference,
)


class FHIRAnnotation(BaseModel):
    model_config = ConfigDict(extra="allow")

    authorReference: FHIRReference | None = None
    authorString: str | None = None
    time: str | None = None
    text: str = Field(..., description="The annotation content.")


class PlainMedicationDispenseNote(AuditFields, BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal DB ID.")
    author_string: str | None = None
    author_reference: PlainMedicationDispenseReference | None = None
    time: datetime | None = None
    text: str
