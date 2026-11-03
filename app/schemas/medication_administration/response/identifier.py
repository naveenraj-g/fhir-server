from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.datatypes import AuditFields, PlainCodingRow
from app.schemas.enums import IdentifierUse


class PlainMedicationAdministrationIdentifierAssigner(BaseModel):
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


class PlainMedicationAdministrationIdentifierType(BaseModel):
    model_config = ConfigDict(extra="allow")

    text: str | None = None
    coding: list[PlainCodingRow] | None = None


class PlainMedicationAdministrationIdentifier(BaseModel):
    model_config = ConfigDict(extra="allow")

    use: IdentifierUse | None = None
    type: PlainMedicationAdministrationIdentifierType | None = None
    system: str | None = None
    value: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    assigner: PlainMedicationAdministrationIdentifierAssigner | None = None


class MedicationAdministrationIdentifierListItem(AuditFields):
    model_config = ConfigDict(extra="allow")

    id: int
    use: str | None = None
    system: str | None = None
    value: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    assigner_id: int | None = None
    assigner_display: str | None = None


class MedicationAdministrationIdentifierListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    data: list[MedicationAdministrationIdentifierListItem]
