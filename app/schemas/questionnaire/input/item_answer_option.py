from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field


class QuestionnaireItemAnswerOptionInput(BaseModel):
    """Questionnaire.item.answerOption (0..*) —
    https://www.hl7.org/fhir/R4/questionnaire-definitions.html#Questionnaire.item.answerOption

    `value[x]` (1..1, choice of integer|date|time|string|Coding|
    Reference(Any)) — one field group per variant."""

    model_config = ConfigDict(extra="forbid")

    value_integer: int | None = Field(None, description="value[x]: integer.")
    value_date: date | None = Field(None, description="value[x]: date.")
    value_time: time | None = Field(None, description="value[x]: time.")
    value_string: str | None = Field(None, description="value[x]: string.")
    value_coding_system: str | None = Field(None, description="value[x]: Coding — system.")
    value_coding_version: str | None = Field(None, description="value[x]: Coding — version.")
    value_coding_code: str | None = Field(None, description="value[x]: Coding — code.")
    value_coding_display: str | None = Field(None, description="value[x]: Coding — display.")
    value_coding_user_selected: bool | None = Field(
        None, description="value[x]: Coding — whether chosen directly by a user."
    )
    value_reference: str | None = Field(
        None, description="value[x]: Reference(Any), as a FHIR reference string."
    )
    value_reference_display: str | None = Field(
        None, description="value[x]: Reference — plain text display."
    )

    initial_selected: bool | None = Field(
        None, description="Whether this option is selected by default."
    )
