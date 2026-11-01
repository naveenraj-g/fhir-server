from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class CommunicationReferenceInput(BaseModel):
    """Reference input for Communication (reference + display + optional logical identifier fallback)."""

    model_config = ConfigDict(extra="forbid")

    reference: str | None = Field(
        None, description="FHIR reference string (e.g. 'Patient/10001')."
    )
    display: str | None = Field(
        None, description="Plain text display narrative for reference."
    )
    identifier_use: IdentifierUse | None = Field(
        None, description="Fallback identifier — purpose/use."
    )
    identifier_type_system: str | None = Field(
        None, description="Fallback identifier — type coding system."
    )
    identifier_type_version: str | None = Field(
        None, description="Fallback identifier — type coding version."
    )
    identifier_type_code: str | None = Field(
        None, description="Fallback identifier — type coding code."
    )
    identifier_type_display: str | None = Field(
        None, description="Fallback identifier — type coding display."
    )
    identifier_type_text: str | None = Field(
        None, description="Fallback identifier — type text."
    )
    identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — type user selected."
    )
    identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace system URL."
    )
    identifier_value: str | None = Field(
        None, description="Fallback identifier — value."
    )
    identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — validity period start."
    )
    identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — validity period end."
    )
