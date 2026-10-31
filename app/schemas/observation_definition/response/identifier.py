from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCodingRow, PlainIdentifierType


class PlainObservationDefinitionIdentifier(BaseModel):
    """Plain (snake_case) ObservationDefinition identifier response."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal DB ID.")
    use: str | None = Field(None, description="Identifier use.")
    system: str | None = Field(None, description="Identifier system.")
    value: str | None = Field(None, description="Identifier value.")
    type_text: str | None = Field(None, description="Type text.")
    type_codings: list[PlainCodingRow] | None = Field(
        None, description="Codings for identifier type."
    )
    period_start: datetime | None = Field(None, description="Start date/time.")
    period_end: datetime | None = Field(None, description="End date/time.")
    assigner: str | None = Field(None, description="Assigner reference string.")
    assigner_display: str | None = Field(None, description="Assigner display name.")
