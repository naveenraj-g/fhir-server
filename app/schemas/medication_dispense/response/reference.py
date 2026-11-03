from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import AuditFields, FHIRIdentifier


class PlainMedicationDispenseReference(AuditFields, BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = Field(None, description="Internal DB ID.")
    reference: str | None = None
    type: str | None = None
    target_id: int | None = Field(None, description="Public target ID.")
    display: str | None = None
    identifier: FHIRIdentifier | None = None
