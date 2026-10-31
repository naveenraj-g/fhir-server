from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRCodeableConcept, FHIRReference, PlainCodingRow
from .reference import PlainConditionEvidenceDetail


class FHIRConditionEvidence(BaseModel):
    """Condition.evidence (0..* BackboneElement) in FHIR R4."""

    code: list[FHIRCodeableConcept] | None = None
    detail: list[FHIRReference] | None = None


class PlainConditionEvidenceCode(BaseModel):
    """Plain response shape for Condition.evidence.code."""

    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal DB ID.")
    text: str | None = Field(None, description="Manifestation text.")
    codings: list[PlainCodingRow] | None = Field(None, description="Codings for manifestation.")


class PlainConditionEvidence(BaseModel):
    """Plain response shape for Condition.evidence."""

    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal DB ID.")
    codes: list[PlainConditionEvidenceCode] | None = Field(None, description="Manifestations/codes.")
    details: list[PlainConditionEvidenceDetail] | None = Field(None, description="Supporting details.")
