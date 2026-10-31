from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput
from app.schemas.enums import IdentifierUse


class FlagIdentifierInput(BaseModel):
    """Flag.identifier — an identifier for this flag (Identifier)."""

    model_config = ConfigDict(extra="forbid")
    use: IdentifierUse | None = Field(
        None,
        description="Identifies the purpose for this identifier, if known — usual|official|temp|secondary|old.",
    )
    type_coding: list[CodingInput] | None = Field(
        None,
        description="Coding(s) for this identifier's type — e.g. MRN, SSN, DL.",
    )
    type_text: str | None = Field(
        None,
        description="A human language representation of the identifier's type.",
    )
    system: str | None = Field(
        None,
        description="Establishes the namespace for the value.",
    )
    value: str | None = Field(
        None,
        description="The portion of the identifier typically relevant to the user.",
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the time period during which this identifier is/was valid for use.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the time period during which this identifier is/was valid for use.",
    )
    assigner: str | None = Field(
        None,
        description="Organization that issued/manages this identifier, as a FHIR reference string (e.g. 'Organization/190001').",
    )
    assigner_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the assigning organization in addition to the reference.",
    )
    assigner_identifier_use: IdentifierUse | None = Field(
        None,
        description="Purpose of assigner identifier.",
    )
    assigner_identifier_type_system: str | None = Field(
        None,
        description="Namespace for assigner identifier type code.",
    )
    assigner_identifier_type_version: str | None = Field(
        None,
        description="Version of assigner identifier type code system.",
    )
    assigner_identifier_type_code: str | None = Field(
        None,
        description="Symbol in syntax defined by assigner identifier type code system.",
    )
    assigner_identifier_type_display: str | None = Field(
        None,
        description="Representation defined by assigner identifier type code system.",
    )
    assigner_identifier_type_text: str | None = Field(
        None,
        description="Plain text representation of assigner identifier type.",
    )
    assigner_identifier_type_user_selected: bool | None = Field(
        None,
        description="If assigner identifier type was chosen by user.",
    )
    assigner_identifier_system: str | None = Field(
        None,
        description="The namespace for the assigner identifier value.",
    )
    assigner_identifier_value: str | None = Field(
        None,
        description="The value of the assigner identifier.",
    )
    assigner_identifier_period_start: datetime | None = Field(
        None,
        description="Start time of assigner identifier validity.",
    )
    assigner_identifier_period_end: datetime | None = Field(
        None,
        description="End time of assigner identifier validity.",
    )
