from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput
from app.schemas.enums import IdentifierUse


class RelatedPersonIdentifierInput(BaseModel):
    """RelatedPerson.identifier — an identifier for this person (Identifier)."""

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
        description="Establishes the namespace for the value — that is, a URL that describes a set of unique values.",
    )
    value: str | None = Field(
        None,
        description="The portion of the identifier typically relevant to the user and which is unique within the context of the system.",
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
        description="Logical-identifier fallback for the assigner — identifies the purpose for that identifier, if known.",
    )
    assigner_identifier_type_system: str | None = Field(
        None, description="Logical-identifier fallback for the assigner — type system URL."
    )
    assigner_identifier_type_version: str | None = Field(
        None, description="Logical-identifier fallback for the assigner — type version."
    )
    assigner_identifier_type_code: str | None = Field(
        None, description="Logical-identifier fallback for the assigner — type code."
    )
    assigner_identifier_type_display: str | None = Field(
        None, description="Logical-identifier fallback for the assigner — type display text."
    )
    assigner_identifier_type_text: str | None = Field(
        None, description="Logical-identifier fallback for the assigner — type free text."
    )
    assigner_identifier_type_user_selected: bool | None = Field(
        None, description="Logical-identifier fallback for the assigner — user selected flag."
    )
    assigner_identifier_system: str | None = Field(
        None, description="Logical-identifier fallback for the assigner — namespace URL."
    )
    assigner_identifier_value: str | None = Field(
        None, description="Logical-identifier fallback for the assigner — value."
    )
    assigner_identifier_period_start: datetime | None = Field(
        None, description="Logical-identifier fallback for the assigner — start of validity period."
    )
    assigner_identifier_period_end: datetime | None = Field(
        None, description="Logical-identifier fallback for the assigner — end of validity period."
    )
