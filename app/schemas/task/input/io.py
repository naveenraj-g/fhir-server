from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IdentifierUse
from app.schemas.datatypes import CodingInput


class TaskInputInput(BaseModel):
    """Information used to perform task."""

    model_config = ConfigDict(extra="forbid")

    type_coding: list[CodingInput] | None = Field(
        None, description="Label for input."
    )
    type_text: str | None = Field(
        None, description="Plain text description for input type."
    )
    value_string: str | None = Field(None, description="String value.")
    value_boolean: bool | None = Field(None, description="Boolean value.")
    value_integer: int | None = Field(None, description="Integer value.")
    value_decimal: float | None = Field(None, description="Decimal value.")
    value_date: date | None = Field(None, description="Date value.")
    value_date_time: datetime | None = Field(None, description="DateTime value.")
    value_time: time | None = Field(None, description="Time value.")
    value_uri: str | None = Field(None, description="URI value.")
    value_code: str | None = Field(None, description="Code value.")
    value_reference: str | None = Field(None, description="Reference string value.")
    value_reference_display: str | None = Field(None, description="Reference display.")
    value_reference_identifier_use: IdentifierUse | None = Field(
        None, description="Purpose of this identifier."
    )
    value_reference_identifier_type_system: str | None = Field(
        None, description="Identity of the terminology system for the identifier type."
    )
    value_reference_identifier_type_version: str | None = Field(
        None, description="Version of the system that defines the identifier type."
    )
    value_reference_identifier_type_code: str | None = Field(
        None, description="Symbol in syntax defined by the system for identifier type."
    )
    value_reference_identifier_type_display: str | None = Field(
        None, description="Representation defined by the system for identifier type."
    )
    value_reference_identifier_type_user_selected: bool | None = Field(
        None, description="If this identifier type coding was chosen directly by the user."
    )
    value_reference_identifier_type_text: str | None = Field(
        None, description="Plain text representation of the identifier type."
    )
    value_reference_identifier_system: str | None = Field(
        None, description="The namespace for the identifier value."
    )
    value_reference_identifier_value: str | None = Field(
        None, description="The portion of the identifier typically relevant to the user."
    )
    value_reference_identifier_period_start: datetime | None = Field(
        None, description="Time period when id is/was valid for use - start."
    )
    value_reference_identifier_period_end: datetime | None = Field(
        None, description="Time period when id is/was valid for use - end."
    )
    value_json: Any | None = Field(None, description="Complex datatype fallback value.")


class TaskOutputInput(BaseModel):
    """Information produced as part of task."""

    model_config = ConfigDict(extra="forbid")

    type_coding: list[CodingInput] | None = Field(
        None, description="Label for output."
    )
    type_text: str | None = Field(
        None, description="Plain text description for output type."
    )
    value_string: str | None = Field(None, description="String value.")
    value_boolean: bool | None = Field(None, description="Boolean value.")
    value_integer: int | None = Field(None, description="Integer value.")
    value_decimal: float | None = Field(None, description="Decimal value.")
    value_date: date | None = Field(None, description="Date value.")
    value_date_time: datetime | None = Field(None, description="DateTime value.")
    value_time: time | None = Field(None, description="Time value.")
    value_uri: str | None = Field(None, description="URI value.")
    value_code: str | None = Field(None, description="Code value.")
    value_reference: str | None = Field(None, description="Reference string value.")
    value_reference_display: str | None = Field(None, description="Reference display.")
    value_reference_identifier_use: IdentifierUse | None = Field(
        None, description="Purpose of this identifier."
    )
    value_reference_identifier_type_system: str | None = Field(
        None, description="Identity of the terminology system for the identifier type."
    )
    value_reference_identifier_type_version: str | None = Field(
        None, description="Version of the system that defines the identifier type."
    )
    value_reference_identifier_type_code: str | None = Field(
        None, description="Symbol in syntax defined by the system for identifier type."
    )
    value_reference_identifier_type_display: str | None = Field(
        None, description="Representation defined by the system for identifier type."
    )
    value_reference_identifier_type_user_selected: bool | None = Field(
        None, description="If this identifier type coding was chosen directly by the user."
    )
    value_reference_identifier_type_text: str | None = Field(
        None, description="Plain text representation of the identifier type."
    )
    value_reference_identifier_system: str | None = Field(
        None, description="The namespace for the identifier value."
    )
    value_reference_identifier_value: str | None = Field(
        None, description="The portion of the identifier typically relevant to the user."
    )
    value_reference_identifier_period_start: datetime | None = Field(
        None, description="Time period when id is/was valid for use - start."
    )
    value_reference_identifier_period_end: datetime | None = Field(
        None, description="Time period when id is/was valid for use - end."
    )
    value_json: Any | None = Field(None, description="Complex datatype fallback value.")
