from datetime import datetime

from pydantic import BaseModel, ConfigDict


class _PlainReferenceRow(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    reference: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    reference_display: str | None = None
    reference_identifier_use: str | None = None
    reference_identifier_type_system: str | None = None
    reference_identifier_type_version: str | None = None
    reference_identifier_type_code: str | None = None
    reference_identifier_type_display: str | None = None
    reference_identifier_type_user_selected: bool | None = None
    reference_identifier_type_text: str | None = None
    reference_identifier_system: str | None = None
    reference_identifier_value: str | None = None
    reference_identifier_period_start: datetime | None = None
    reference_identifier_period_end: datetime | None = None


class PlainMedicationStatementBasedOn(_PlainReferenceRow):
    pass


class PlainMedicationStatementPartOf(_PlainReferenceRow):
    pass


class PlainMedicationStatementDerivedFrom(_PlainReferenceRow):
    pass


class PlainMedicationStatementReasonReference(_PlainReferenceRow):
    pass


class _PlainSingleReferenceRow(BaseModel):
    model_config = ConfigDict(extra="allow")

    reference: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    reference_display: str | None = None
    reference_identifier_use: str | None = None
    reference_identifier_type_system: str | None = None
    reference_identifier_type_version: str | None = None
    reference_identifier_type_code: str | None = None
    reference_identifier_type_display: str | None = None
    reference_identifier_type_user_selected: bool | None = None
    reference_identifier_type_text: str | None = None
    reference_identifier_system: str | None = None
    reference_identifier_value: str | None = None
    reference_identifier_period_start: datetime | None = None
    reference_identifier_period_end: datetime | None = None


class PlainMedicationStatementSubject(_PlainSingleReferenceRow):
    pass


class PlainMedicationStatementMedicationReference(_PlainSingleReferenceRow):
    pass


class PlainMedicationStatementContext(_PlainSingleReferenceRow):
    pass


class PlainMedicationStatementInformationSource(_PlainSingleReferenceRow):
    pass
