from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import AttachmentInput
from app.schemas.enums import IdentifierUse, QuestionnaireResponseQuantityComparator


class QuestionnaireResponseAnswerInput(BaseModel):
    """QuestionnaireResponse.item.answer (0..*) —
    https://www.hl7.org/fhir/R4/questionnaireresponse-definitions.html#QuestionnaireResponse.item.answer

    `value[x]` (0..1, choice of boolean|decimal|integer|date|dateTime|time|
    string|uri|Attachment|Coding|Quantity|Reference(Any)) — the same
    12-variant shape as
    app.schemas.questionnaire.input.item_initial.QuestionnaireItemInitialInput's
    own value[x]; one field group per variant.

    `item` (0..*, recursive) nests QuestionnaireResponseItemInput beneath
    this specific answer — mutually recursive with that class's own
    `item` field. Must call `model_rebuild()` after both classes are
    defined (done in item.py, which imports this module last) so the
    forward reference resolves."""

    model_config = ConfigDict(extra="forbid")

    value_boolean: bool | None = Field(None, description="value[x]: boolean.")
    value_decimal: float | None = Field(None, description="value[x]: decimal.")
    value_integer: int | None = Field(None, description="value[x]: integer.")
    value_date: date | None = Field(None, description="value[x]: date.")
    value_date_time: datetime | None = Field(None, description="value[x]: dateTime.")
    value_time: time | None = Field(None, description="value[x]: time.")
    value_string: str | None = Field(None, description="value[x]: string.")
    value_uri: str | None = Field(None, description="value[x]: uri.")
    value_attachment: AttachmentInput | None = Field(None, description="value[x]: Attachment.")
    value_coding_system: str | None = Field(None, description="value[x]: Coding — system.")
    value_coding_version: str | None = Field(None, description="value[x]: Coding — version.")
    value_coding_code: str | None = Field(None, description="value[x]: Coding — code.")
    value_coding_display: str | None = Field(None, description="value[x]: Coding — display.")
    value_coding_user_selected: bool | None = Field(
        None, description="value[x]: Coding — whether chosen directly by a user."
    )
    value_quantity_value: float | None = Field(None, description="value[x]: Quantity — numeric value.")
    value_quantity_comparator: QuestionnaireResponseQuantityComparator | None = Field(
        None, description="value[x]: Quantity — < | <= | >= | >."
    )
    value_quantity_unit: str | None = Field(None, description="value[x]: Quantity — unit representation.")
    value_quantity_system: str | None = Field(None, description="value[x]: Quantity — unit system.")
    value_quantity_code: str | None = Field(None, description="value[x]: Quantity — coded unit form.")
    value_reference: str | None = Field(
        None, description="value[x]: Reference(Any), as a FHIR reference string."
    )
    value_reference_display: str | None = Field(None, description="value[x]: Reference — plain text display.")
    value_reference_identifier_use: IdentifierUse | None = Field(
        None, description="Fallback identifier — identifies its purpose, if known."
    )
    value_reference_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — code system for its type."
    )
    value_reference_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type code system."
    )
    value_reference_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — a symbol for its type."
    )
    value_reference_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    value_reference_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — whether its type was user-selected."
    )
    value_reference_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )
    value_reference_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    value_reference_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    value_reference_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    value_reference_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of validity period."
    )

    item: list["QuestionnaireResponseItemInput"] | None = Field(
        None, description="Nested items under this specific answer."
    )
