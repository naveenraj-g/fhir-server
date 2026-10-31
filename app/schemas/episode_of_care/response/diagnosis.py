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
    condition: str
    condition_display: str | None = None
    role_text: str | None = None
    role_codings: list[PlainCodingRow] = []
    rank: int | None = None
