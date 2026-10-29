from pydantic import Field

from app.schemas.datatypes import AuditFields


class PlainQuestionnaireItemAnswerOption(AuditFields):
    id: int = Field(..., description="Internal row ID.")

    value_integer: int | None = Field(None, description="value[x]: integer.")
    value_date: str | None = Field(None, description="value[x]: date.")
    value_time: str | None = Field(None, description="value[x]: time.")
    value_string: str | None = Field(None, description="value[x]: string.")
    value_coding_system: str | None = Field(None, description="value[x]: Coding — system.")
    value_coding_version: str | None = Field(None, description="value[x]: Coding — version.")
    value_coding_code: str | None = Field(None, description="value[x]: Coding — code.")
    value_coding_display: str | None = Field(None, description="value[x]: Coding — display.")
    value_coding_user_selected: bool | None = Field(None, description="value[x]: Coding — whether chosen directly by a user.")
    value_reference: str | None = Field(None, description="Resolved FHIR reference.")
    value_reference_type: str | None = Field(None, description="Resolved reference target type.")
    value_reference_id: int | None = Field(None, description="Internal ID of the resolved target, if any.")
    value_reference_display: str | None = Field(None, description="value[x]: Reference — plain text display.")

    initial_selected: bool | None = Field(None, description="Whether this option is selected by default.")
