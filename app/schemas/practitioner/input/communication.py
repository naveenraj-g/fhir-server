from pydantic import BaseModel, ConfigDict, Field


class PractitionerCommunicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language_system: str = Field(..., description="URI of the language code system.")
    language_version: str | None = Field(
        None, description="Version of the language code system."
    )
    language_code: str = Field(
        ..., description="ISO-639-1 language code (e.g. en, fr, de)."
    )
    language_display: str = Field(
        ..., description="Human-readable display for the language."
    )
    language_text: str | None = None
    language_user_selected: bool | None = Field(
        None,
        description="Whether this language coding was chosen directly by the user.",
    )


class PractitionerCommunicationPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language_system: str | None = None
    language_version: str | None = None
    language_code: str | None = None
    language_display: str | None = None
    language_text: str | None = None
    language_user_selected: bool | None = None
