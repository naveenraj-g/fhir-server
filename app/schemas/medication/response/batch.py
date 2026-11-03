from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FHIRMedicationBatch(BaseModel):
    """Medication.batch (0..1 BackboneElement) in FHIR R4."""

    model_config = ConfigDict(extra="allow")

    lotNumber: str | None = Field(None, description="Identifier assigned to batch.")
    expirationDate: str | None = Field(None, description="When batch will expire.")


class PlainMedicationBatch(BaseModel):
    """Medication.batch in plain snake_case."""

    model_config = ConfigDict(extra="allow")

    lot_number: str | None = None
    expiration_date: datetime | None = None
