from pydantic import Field

from app.schemas.datatypes import AuditFields, PlainAttachmentRow


class PlainQuestionnaireItemInitial(AuditFields):
    id: int = Field(..., description="Internal row ID.")

    value_boolean: bool | None = Field(None, description="value[x]: boolean.")
    value_decimal: float | None = Field(None, description="value[x]: decimal.")
    value_integer: int | None = Field(None, description="value[x]: integer.")
    value_date: str | None = Field(None, description="value[x]: date.")
    value_date_time: str | None = Field(None, description="value[x]: dateTime.")
    value_time: str | None = Field(None, description="value[x]: time.")
    value_string: str | None = Field(None, description="value[x]: string.")
    value_uri: str | None = Field(None, description="value[x]: uri.")
    value_attachment: PlainAttachmentRow | None = Field(None, description="value[x]: Attachment.")
    value_coding_system: str | None = Field(None, description="value[x]: Coding — system.")
    value_coding_version: str | None = Field(None, description="value[x]: Coding — version.")
    value_coding_code: str | None = Field(None, description="value[x]: Coding — code.")
    value_coding_display: str | None = Field(None, description="value[x]: Coding — display.")
    value_coding_user_selected: bool | None = Field(None, description="value[x]: Coding — whether chosen directly by a user.")
    value_quantity_value: float | None = Field(None, description="value[x]: Quantity — numeric value.")
    value_quantity_comparator: str | None = Field(None, description="value[x]: Quantity — < | <= | >= | >.")
    value_quantity_unit: str | None = Field(None, description="value[x]: Quantity — unit representation.")
    value_quantity_system: str | None = Field(None, description="value[x]: Quantity — unit system.")
    value_quantity_code: str | None = Field(None, description="value[x]: Quantity — coded unit form.")
    value_reference: str | None = Field(None, description="Resolved FHIR reference.")
    value_reference_type: str | None = Field(None, description="Resolved reference target type.")
    value_reference_id: int | None = Field(None, description="Internal ID of the resolved target, if any.")
    value_reference_display: str | None = Field(None, description="value[x]: Reference — plain text display.")
