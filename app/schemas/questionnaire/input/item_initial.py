from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import AttachmentInput
from app.schemas.enums import QuestionnaireQuantityComparator


class QuestionnaireItemInitialInput(BaseModel):
    """Questionnaire.item.initial (0..*) —
    https://www.hl7.org/fhir/R4/questionnaire-definitions.html#Questionnaire.item.initial

    `value[x]` (1..1, choice of boolean|decimal|integer|date|dateTime|time|
    string|uri|Attachment|Coding|Quantity|Reference(Any)) — the most
    polymorphic choice type in this codebase; one field group per variant.
    The Attachment variant reuses the shared app.schemas.datatypes
    AttachmentInput rather than redeclaring its 8 sub-fields."""

    model_config = ConfigDict(extra="forbid")

    value_boolean: bool | None = Field(None, description="value[x]: boolean.")
    value_decimal: float | None = Field(None, description="value[x]: decimal.")
    value_integer: int | None = Field(None, description="value[x]: integer.")
    value_date: date | None = Field(None, description="value[x]: date.")
    value_date_time: datetime | None = Field(None, description="value[x]: dateTime.")
    value_time: time | None = Field(None, description="value[x]: time.")
    value_string: str | None = Field(None, description="value[x]: string.")
    value_uri: str | None = Field(None, description="value[x]: uri.")
    value_attachment: AttachmentInput | None = Field(
        None, description="value[x]: Attachment."
    )
    value_coding_system: str | None = Field(None, description="value[x]: Coding — system.")
    value_coding_version: str | None = Field(None, description="value[x]: Coding — version.")
    value_coding_code: str | None = Field(None, description="value[x]: Coding — code.")
    value_coding_display: str | None = Field(None, description="value[x]: Coding — display.")
    value_coding_user_selected: bool | None = Field(
        None, description="value[x]: Coding — whether chosen directly by a user."
    )
    value_quantity_value: float | None = Field(None, description="value[x]: Quantity — numeric value.")
    value_quantity_comparator: QuestionnaireQuantityComparator | None = Field(
        None, description="value[x]: Quantity — < | <= | >= | >."
    )
    value_quantity_unit: str | None = Field(None, description="value[x]: Quantity — unit representation.")
    value_quantity_system: str | None = Field(None, description="value[x]: Quantity — unit system.")
    value_quantity_code: str | None = Field(None, description="value[x]: Quantity — coded unit form.")
    value_reference: str | None = Field(
        None, description="value[x]: Reference(Any), as a FHIR reference string."
    )
    value_reference_display: str | None = Field(
        None, description="value[x]: Reference — plain text display."
    )
