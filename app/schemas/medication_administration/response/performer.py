from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import AuditFields, FHIRCodeableConcept, FHIRReference
from app.schemas.enums import IdentifierUse
from app.schemas.medication_administration.response.codeable_concept import (
    PlainMedicationAdministrationCodeableConcept,
)


class FHIRMedicationAdministrationPerformer(BaseModel):
    model_config = ConfigDict(extra="allow")

    function: FHIRCodeableConcept | None = Field(None, description="Type of performance.")
    actor: FHIRReference = Field(..., description="Who performed the administration.")


class PlainMedicationAdministrationPerformerActor(BaseModel):
    model_config = ConfigDict(extra="allow")

    reference: str | None = None
    type: str | None = None
    id: int | None = None
    display: str | None = None
    identifier_use: IdentifierUse | None = None
    identifier_type_system: str | None = None
    identifier_type_version: str | None = None
    identifier_type_code: str | None = None
    identifier_type_display: str | None = None
    identifier_type_user_selected: bool | None = None
    identifier_type_text: str | None = None
    identifier_system: str | None = None
    identifier_value: str | None = None
    identifier_period_start: datetime | None = None
    identifier_period_end: datetime | None = None


class PlainMedicationAdministrationPerformer(BaseModel):
    model_config = ConfigDict(extra="allow")

    function: PlainMedicationAdministrationCodeableConcept | None = None
    actor: PlainMedicationAdministrationPerformerActor


class MedicationAdministrationPerformerListItem(AuditFields):
    model_config = ConfigDict(extra="allow")

    id: int
    function_text: str | None = None
    actor_reference: str | None = None
    actor_type: str | None = None
    actor_id: int | None = None
    actor_display: str | None = None


class MedicationAdministrationPerformerListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    data: list[MedicationAdministrationPerformerListItem]
