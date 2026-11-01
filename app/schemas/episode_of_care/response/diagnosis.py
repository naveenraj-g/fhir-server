from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.datatypes import (
    AuditFields,
    FHIRCodeableConcept,
    FHIRReference,
    PlainCodingRow,
)


class FHIRDiagnosis(BaseModel):
    """FHIR representation of EpisodeOfCare.diagnosis."""

    model_config = ConfigDict(extra="forbid")

    condition: FHIRReference
    role: FHIRCodeableConcept | None = None
    rank: int | None = None


class PlainEpisodeOfCareDiagnosis(AuditFields, BaseModel):
    """Plain response representation of EpisodeOfCare diagnosis."""

    model_config = ConfigDict(extra="forbid")

    id: int
    condition: str | None = None
    condition_id: int | None = None
    condition_type: str | None = None
    condition_display: str | None = None
    condition_identifier_use: str | None = None
    condition_identifier_type_system: str | None = None
    condition_identifier_type_version: str | None = None
    condition_identifier_type_code: str | None = None
    condition_identifier_type_display: str | None = None
    condition_identifier_type_user_selected: bool | None = None
    condition_identifier_type_text: str | None = None
    condition_identifier_system: str | None = None
    condition_identifier_value: str | None = None
    condition_identifier_period_start: datetime | None = None
    condition_identifier_period_end: datetime | None = None
    role_text: str | None = None
    role_codings: list[PlainCodingRow] = []
    rank: int | None = None
