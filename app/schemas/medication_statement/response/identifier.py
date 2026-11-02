from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.medication_statement.response.codeable_concept import (
    PlainMedicationStatementCode,
)


class PlainMedicationStatementIdentifier(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    use: str | None = None
    type_text: str | None = None
    system: str | None = None
    value: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None

    assigner_reference: str | None = None
    assigner_type: str | None = None
    assigner_id: int | None = None
    assigner_display: str | None = None
    assigner_identifier_use: str | None = None
    assigner_identifier_type_system: str | None = None
    assigner_identifier_type_version: str | None = None
    assigner_identifier_type_code: str | None = None
    assigner_identifier_type_display: str | None = None
    assigner_identifier_type_user_selected: bool | None = None
    assigner_identifier_type_text: str | None = None
    assigner_identifier_system: str | None = None
    assigner_identifier_value: str | None = None
    assigner_identifier_period_start: datetime | None = None
    assigner_identifier_period_end: datetime | None = None

    type_codings: list[PlainMedicationStatementCode] | None = None
