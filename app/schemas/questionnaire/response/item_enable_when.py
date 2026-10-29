from pydantic import Field

from app.schemas.datatypes import AuditFields


class PlainQuestionnaireItemEnableWhen(AuditFields):
    id: int = Field(..., description="Internal row ID.")
    question: str = Field(..., description="The linkId of the question whose answer this condition is based on.")
    operator: str = Field(..., description="exists | = | != | > | < | >= | <=.")

    answer_boolean: bool | None = Field(None, description="answer[x]: boolean.")
    answer_decimal: float | None = Field(None, description="answer[x]: decimal.")
    answer_integer: int | None = Field(None, description="answer[x]: integer.")
    answer_date: str | None = Field(None, description="answer[x]: date.")
    answer_date_time: str | None = Field(None, description="answer[x]: dateTime.")
    answer_time: str | None = Field(None, description="answer[x]: time.")
    answer_string: str | None = Field(None, description="answer[x]: string.")
    answer_coding_system: str | None = Field(None, description="answer[x]: Coding — system.")
    answer_coding_version: str | None = Field(None, description="answer[x]: Coding — version.")
    answer_coding_code: str | None = Field(None, description="answer[x]: Coding — code.")
    answer_coding_display: str | None = Field(None, description="answer[x]: Coding — display.")
    answer_coding_user_selected: bool | None = Field(None, description="answer[x]: Coding — whether chosen directly by a user.")
    answer_quantity_value: float | None = Field(None, description="answer[x]: Quantity — numeric value.")
    answer_quantity_comparator: str | None = Field(None, description="answer[x]: Quantity — < | <= | >= | >.")
    answer_quantity_unit: str | None = Field(None, description="answer[x]: Quantity — unit representation.")
    answer_quantity_system: str | None = Field(None, description="answer[x]: Quantity — unit system.")
    answer_quantity_code: str | None = Field(None, description="answer[x]: Quantity — coded unit form.")
    answer_reference: str | None = Field(None, description="Resolved FHIR reference, e.g. 'Patient/10001'.")
    answer_reference_type: str | None = Field(None, description="Resolved reference target type.")
    answer_reference_id: int | None = Field(None, description="Internal ID of the resolved target, if any.")
    answer_reference_display: str | None = Field(None, description="answer[x]: Reference — plain text display.")
