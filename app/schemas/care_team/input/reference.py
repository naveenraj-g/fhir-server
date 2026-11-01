from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class CareTeamReferenceInput(BaseModel):
    """Reference input for CareTeam (reference + narrative display + logical identifier fallback)."""

    model_config = ConfigDict(extra="forbid")

    reference: str | None = Field(
        None, description="FHIR reference string (e.g. 'Condition/120001')."
    )
    display: str | None = Field(
        None, description="Plain text display narrative for reference."
    )
    identifier_use: IdentifierUse | None = Field(
        None, description="Purpose of this identifier."
    )
    identifier_type_system: str | None = Field(
        None, description="Identity of the terminology system for the identifier type."
    )
    identifier_type_version: str | None = Field(
        None, description="Version of the system that defines the identifier type."
    )
    identifier_type_code: str | None = Field(
        None, description="Symbol in syntax defined by the system for identifier type."
    )
    identifier_type_display: str | None = Field(
        None, description="Representation defined by the system for identifier type."
    )
    identifier_type_user_selected: bool | None = Field(
        None, description="If this identifier type coding was chosen directly by the user."
    )
    identifier_type_text: str | None = Field(
        None, description="Plain text representation of the identifier type."
    )
    identifier_system: str | None = Field(
        None, description="The namespace for the identifier value."
    )
    identifier_value: str | None = Field(
        None, description="The portion of the identifier typically relevant to the user."
    )
    identifier_period_start: datetime | None = Field(
        None, description="Time period when id is/was valid for use - start."
    )
    identifier_period_end: datetime | None = Field(
        None, description="Time period when id is/was valid for use - end."
    )
