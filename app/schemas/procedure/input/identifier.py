from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput
from app.schemas.enums import IdentifierUse


class ProcedureIdentifierInput(BaseModel):
    """Procedure.identifier (0..*)."""

    model_config = ConfigDict(extra="forbid")

    use: IdentifierUse | None = Field(
        None, description="usual | official | temp | secondary | old."
    )
    type_coding: list[CodingInput] | None = Field(
        None, description="Coding(s) for this identifier's type."
    )
    type_text: str | None = Field(
        None, description="A human language representation of the identifier's type."
    )
    system: str | None = Field(
        None, description="Establishes the namespace for the value."
    )
    value: str | None = Field(
        None, description="The portion typically relevant to the user, unique within the system."
    )
    period_start: datetime | None = Field(
        None, description="Start of the identifier's validity period."
    )
    period_end: datetime | None = Field(
        None, description="End of the identifier's validity period."
    )
    assigner: str | None = Field(
        None, description="Organization that issued/manages this identifier, as a FHIR reference string (e.g. Organization/123)."
    )
    assigner_display: str | None = Field(
        None, description="Plain text narrative identifying the assigning organization."
    )
