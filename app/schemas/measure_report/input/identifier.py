from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IdentifierUse
from app.schemas.datatypes import CodingInput


class MeasureReportIdentifierInput(BaseModel):
    """MeasureReport.identifier input schema."""

    model_config = ConfigDict(extra="forbid")

    use: IdentifierUse | None = Field(
        None, description="usual | official | temp | secondary | old."
    )
    system: str | None = Field(
        None, description="The namespace for the identifier value."
    )
    value: str | None = Field(None, description="The value that is unique.")
    type_text: str | None = Field(
        None, description="Description of identifier type."
    )
    type_coding: list[CodingInput] | None = Field(
        None, description="Coding for identifier type."
    )
    period_start: datetime | None = Field(
        None, description="Time period when id is/was valid for use."
    )
    period_end: datetime | None = Field(
        None, description="Time period when id is/was valid for use."
    )
    assigner: str | None = Field(
        None, description="Organization that issued id (Organization/123)."
    )
    assigner_display: str | None = Field(
        None, description="Organization display text."
    )

    # Assigner fallback identifier
    assigner_identifier_use: IdentifierUse | None = Field(
        None, description="Fallback identifier — use."
    )
    assigner_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — type system."
    )
    assigner_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — type version."
    )
    assigner_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — type code."
    )
    assigner_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — type display."
    )
    assigner_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — type user selected."
    )
    assigner_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — type text."
    )
    assigner_identifier_system: str | None = Field(
        None, description="Fallback identifier — system."
    )
    assigner_identifier_value: str | None = Field(
        None, description="Fallback identifier — value."
    )
    assigner_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — period start."
    )
    assigner_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — period end."
    )
