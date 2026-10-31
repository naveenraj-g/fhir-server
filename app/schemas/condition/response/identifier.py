from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCodingRow
from app.schemas.enums import IdentifierUse


class PlainConditionIdentifier(BaseModel):
    """Plain response shape for Condition.identifier."""

    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal DB ID.")
    use: IdentifierUse | None = Field(None, description="usual | official | temp | secondary | old.")
    type_text: str | None = Field(None, description="A human language representation of the identifier's type.")
    type_codings: list[PlainCodingRow] | None = Field(None, description="Coding(s) for this identifier's type.")
    system: str | None = Field(None, description="Establishes the namespace for the value.")
    value: str | None = Field(None, description="The portion typically relevant to the user, unique within the system.")
    period_start: str | None = Field(None, description="Start of the identifier's validity period.")
    period_end: str | None = Field(None, description="End of the identifier's validity period.")
    assigner_reference: str | None = Field(None, description="FHIR reference string for assigning organization.")
    assigner_id: int | None = Field(None, description="Target organization's public sequence ID.")
    assigner_type: str | None = Field(None, description="Target resource type (Organization).")
    assigner_display: str | None = Field(None, description="Narrative display for assigning organization.")
