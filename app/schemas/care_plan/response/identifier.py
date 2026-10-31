from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCodingRow


class PlainCarePlanIdentifier(BaseModel):
    """Plain response shape for CarePlan.identifier."""

    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal DB ID.")
    use: str | None = Field(None, description="Identifier use.")
    type_text: str | None = Field(None, description="Identifier type text.")
    system: str | None = Field(None, description="System URL.")
    value: str | None = Field(None, description="Identifier value.")
    period_start: str | None = Field(None, description="Period start.")
    period_end: str | None = Field(None, description="Period end.")
    assigner_id: int | None = Field(None, description="Assigner Organization public ID.")
    assigner_display: str | None = Field(None, description="Assigner display.")
    type_codings: list[PlainCodingRow] | None = Field(
        None, description="Codings for identifier type."
    )
