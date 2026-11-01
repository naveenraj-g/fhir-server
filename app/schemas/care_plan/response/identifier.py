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
    assigner_identifier_use: str | None = Field(None, description="Assigner identifier use.")
    assigner_identifier_type_system: str | None = Field(None, description="Assigner identifier type system.")
    assigner_identifier_type_version: str | None = Field(None, description="Assigner identifier type version.")
    assigner_identifier_type_code: str | None = Field(None, description="Assigner identifier type code.")
    assigner_identifier_type_display: str | None = Field(None, description="Assigner identifier type display.")
    assigner_identifier_type_user_selected: bool | None = Field(None, description="Assigner identifier type user selected.")
    assigner_identifier_type_text: str | None = Field(None, description="Assigner identifier type text.")
    assigner_identifier_system: str | None = Field(None, description="Assigner identifier system.")
    assigner_identifier_value: str | None = Field(None, description="Assigner identifier value.")
    assigner_identifier_period_start: str | None = Field(None, description="Assigner identifier period start.")
    assigner_identifier_period_end: str | None = Field(None, description="Assigner identifier period end.")
    type_codings: list[PlainCodingRow] | None = Field(
        None, description="Codings for identifier type."
    )
