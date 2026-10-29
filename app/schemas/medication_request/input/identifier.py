from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput
from app.schemas.enums import IdentifierUse


class MedicationRequestIdentifierInput(BaseModel):
    """Shared shape for MedicationRequest.identifier (0..* — used as a
    list item) AND MedicationRequest.groupIdentifier (0..1 — used as a
    single nested field); both are plain Identifier, field-for-field
    identical. Mirrors
    app.schemas.service_request.input.identifier.ServiceRequestIdentifierInput."""

    model_config = ConfigDict(extra="forbid")
    use: IdentifierUse | None = Field(None, description="usual|official|temp|secondary|old.")
    type_coding: list[CodingInput] | None = Field(None, description="Coding(s) for this identifier's type.")
    type_text: str | None = Field(None, description="A human language representation of the identifier's type.")
    system: str | None = Field(None, description="Establishes the namespace for the value.")
    value: str | None = Field(None, description="The portion typically relevant to the user, unique within the system.")
    period_start: datetime | None = Field(None, description="Start of the identifier's validity period.")
    period_end: datetime | None = Field(None, description="End of the identifier's validity period.")
    assigner: str | None = Field(None, description="Organization that issued/manages this identifier, as a FHIR reference string.")
    assigner_display: str | None = Field(None, description="Plain text narrative identifying the assigning organization.")
    assigner_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — its purpose, if known.")
    assigner_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    assigner_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    assigner_identifier_type_code: str | None = Field(None, description="Fallback identifier — a symbol for its type.")
    assigner_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    assigner_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    assigner_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether its type was user-selected.")
    assigner_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    assigner_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    assigner_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — start of validity period.")
    assigner_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — end of validity period.")
