from pydantic import BaseModel, ConfigDict, Field


class CommunicationCreate(BaseModel):
    """FHIR R4 Patient.communication BackboneElement — a language the patient can use
    for healthcare-related communication."""

    model_config = ConfigDict(extra="forbid")
    language_system: str | None = Field(
        None,
        description=(
            "CodeableConcept.coding.system for the language (e.g. urn:ietf:bcp:47)."
        ),
    )
    language_version: str | None = Field(
        None,
        description="CodeableConcept.coding.version — version of the language coding system.",
    )
    language_code: str = Field(
        ...,
        description="ISO-639-1 language code (e.g. en, fr, de), optionally region-qualified (e.g. en-US).",
    )
    language_display: str | None = Field(
        None,
        description="CodeableConcept.coding.display — human-readable name of the language.",
    )
    language_text: str | None = Field(
        None,
        description="CodeableConcept.text — plain-text rendering of the language concept.",
    )
    language_user_selected: bool | None = Field(
        None,
        description="CodeableConcept.coding.userSelected — whether this coding was chosen directly by the user.",
    )
    preferred: bool | None = Field(
        None,
        description="True if this language is the patient's preferred language for communication.",
    )


class CommunicationPatch(BaseModel):
    """Partial update to a communication-language entry — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")
    language_system: str | None = Field(
        None, description="URI of the language code system."
    )
    language_version: str | None = Field(
        None, description="Version of the language code system."
    )
    language_code: str | None = Field(
        None, description="ISO-639-1 language code (e.g. en, fr, de)."
    )
    language_display: str | None = Field(
        None, description="Human-readable name of the language."
    )
    language_text: str | None = Field(
        None, description="Plain-text rendering of the language concept."
    )
    language_user_selected: bool | None = Field(
        None, description="Whether this coding was chosen directly by the user."
    )
    preferred: bool | None = Field(
        None, description="True if this is the patient's preferred language."
    )
