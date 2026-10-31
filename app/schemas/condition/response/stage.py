from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRCodeableConcept, FHIRReference, PlainCodingRow
from .reference import PlainConditionStageAssessment


class FHIRConditionStage(BaseModel):
    """Condition.stage (0..* BackboneElement) in FHIR R4."""

    summary: FHIRCodeableConcept | None = None
    assessment: list[FHIRReference] | None = None
    type: FHIRCodeableConcept | None = None


class PlainConditionStage(BaseModel):
    """Plain response shape for Condition.stage."""

    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal DB ID.")
    summary_text: str | None = Field(None, description="Summary text.")
    summary_codings: list[PlainCodingRow] | None = Field(None, description="Codings for summary.")
    type_text: str | None = Field(None, description="Staging type text.")
    type_codings: list[PlainCodingRow] | None = Field(None, description="Codings for staging type.")
    assessments: list[PlainConditionStageAssessment] | None = Field(None, description="Assessments.")
