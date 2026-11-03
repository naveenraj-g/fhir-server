from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MedicationBatchInput(BaseModel):
    """Medication.batch (0..1 BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    lot_number: str | None = Field(None, description="Identifier assigned to batch.")
    expiration_date: datetime | None = Field(None, description="When batch will expire.")
