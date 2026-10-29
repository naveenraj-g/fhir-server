from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import QuestionnaireItemOperator, QuestionnaireQuantityComparator


class QuestionnaireItemEnableWhenInput(BaseModel):
    """Questionnaire.item.enableWhen (0..*) —
    https://www.hl7.org/fhir/R4/questionnaire-definitions.html#Questionnaire.item.enableWhen

    `answer[x]` (1..1, choice of boolean|decimal|integer|date|dateTime|
    time|string|Coding|Quantity|Reference(Any)) — one field group per
    variant; exactly one should be populated."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., description="The linkId of the question whose answer this condition is based on.")
    operator: QuestionnaireItemOperator = Field(
        ..., description="exists | = | != | > | < | >= | <=."
    )

    answer_boolean: bool | None = Field(None, description="answer[x]: boolean.")
    answer_decimal: float | None = Field(None, description="answer[x]: decimal.")
    answer_integer: int | None = Field(None, description="answer[x]: integer.")
    answer_date: date | None = Field(None, description="answer[x]: date.")
    answer_date_time: datetime | None = Field(None, description="answer[x]: dateTime.")
    answer_time: time | None = Field(None, description="answer[x]: time.")
    answer_string: str | None = Field(None, description="answer[x]: string.")
    answer_coding_system: str | None = Field(None, description="answer[x]: Coding — system.")
    answer_coding_version: str | None = Field(None, description="answer[x]: Coding — version.")
    answer_coding_code: str | None = Field(None, description="answer[x]: Coding — code.")
    answer_coding_display: str | None = Field(None, description="answer[x]: Coding — display.")
    answer_coding_user_selected: bool | None = Field(
        None, description="answer[x]: Coding — whether chosen directly by a user."
    )
    answer_quantity_value: float | None = Field(None, description="answer[x]: Quantity — numeric value.")
    answer_quantity_comparator: QuestionnaireQuantityComparator | None = Field(
        None, description="answer[x]: Quantity — < | <= | >= | >."
    )
    answer_quantity_unit: str | None = Field(None, description="answer[x]: Quantity — unit representation.")
    answer_quantity_system: str | None = Field(None, description="answer[x]: Quantity — unit system.")
    answer_quantity_code: str | None = Field(None, description="answer[x]: Quantity — coded unit form.")
    answer_reference: str | None = Field(
        None, description="answer[x]: Reference(Any), as a FHIR reference string."
    )
    answer_reference_display: str | None = Field(
        None, description="answer[x]: Reference — plain text display."
    )
