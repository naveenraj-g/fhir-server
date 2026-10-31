from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRCodeableConcept, PlainCodingRow


class FHIRActivityDefinitionParticipant(BaseModel):
    """FHIR R4 ActivityDefinition.participant."""

    model_config = ConfigDict(extra="allow")

    type: str | None = None
    role: FHIRCodeableConcept | None = None


class PlainActivityDefinitionParticipant(BaseModel):
    """Plain ActivityDefinition.participant representation."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    type: str = Field(..., description="Participant type.")
    role_text: str | None = None
    role_codings: list[PlainCodingRow] | None = None
