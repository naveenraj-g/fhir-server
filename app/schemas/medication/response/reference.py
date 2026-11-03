from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlainMedicationReference(BaseModel):
    model_config = ConfigDict(extra="allow")

    reference: str | None = None
    type: str | None = None
    id: int | None = None
    display: str | None = None

    identifier_use: str | None = None
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
