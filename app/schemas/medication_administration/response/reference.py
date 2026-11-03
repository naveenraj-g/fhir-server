from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.datatypes import AuditFields
from app.schemas.enums import IdentifierUse


class PlainMedicationAdministrationReference(BaseModel):
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


class _ReferenceListItem(AuditFields):
    model_config = ConfigDict(extra="allow")

    id: int
    reference_reference: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    reference_display: str | None = None


class MedicationAdministrationPartOfListItem(_ReferenceListItem):
    pass


class MedicationAdministrationPartOfListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    data: list[MedicationAdministrationPartOfListItem]


class MedicationAdministrationSupportingInfoListItem(_ReferenceListItem):
    pass


class MedicationAdministrationSupportingInfoListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    data: list[MedicationAdministrationSupportingInfoListItem]


class MedicationAdministrationReasonReferenceListItem(_ReferenceListItem):
    pass


class MedicationAdministrationReasonReferenceListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    data: list[MedicationAdministrationReasonReferenceListItem]


class MedicationAdministrationDeviceListItem(_ReferenceListItem):
    pass


class MedicationAdministrationDeviceListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    data: list[MedicationAdministrationDeviceListItem]


class MedicationAdministrationEventHistoryListItem(_ReferenceListItem):
    pass


class MedicationAdministrationEventHistoryListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    data: list[MedicationAdministrationEventHistoryListItem]
