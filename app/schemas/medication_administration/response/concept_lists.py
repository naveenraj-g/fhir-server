from pydantic import BaseModel, ConfigDict

from app.schemas.datatypes import AuditFields


class MedicationAdministrationStatusReasonListItem(AuditFields):
    model_config = ConfigDict(extra="allow")

    id: int
    text: str | None = None


class MedicationAdministrationStatusReasonListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    data: list[MedicationAdministrationStatusReasonListItem]


class MedicationAdministrationReasonCodeListItem(AuditFields):
    model_config = ConfigDict(extra="allow")

    id: int
    text: str | None = None


class MedicationAdministrationReasonCodeListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    data: list[MedicationAdministrationReasonCodeListItem]
