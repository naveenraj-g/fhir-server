from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import AuditFields, PlainCodingRow
from app.schemas.datatypes.codeable_concept import FHIRCodeableConcept


class FHIRTaskInput(BaseModel):
    """FHIR R4 Task.input element."""

    model_config = ConfigDict(extra="allow")

    type: FHIRCodeableConcept


class FHIRTaskOutput(BaseModel):
    """FHIR R4 Task.output element."""

    model_config = ConfigDict(extra="allow")

    type: FHIRCodeableConcept


class PlainTaskInput(AuditFields):
    """Plain snake_case serialization of a Task input child row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="DB primary key of this input row.")
    type_text: str | None = None
    type_codings: list[PlainCodingRow] | None = None
    value_string: str | None = None
    value_boolean: bool | None = None
    value_integer: int | None = None
    value_decimal: float | None = None
    value_date: str | None = None
    value_date_time: str | None = None
    value_time: str | None = None
    value_uri: str | None = None
    value_code: str | None = None
    value_reference_reference: str | None = None
    value_reference: str | None = None
    value_reference_type: str | None = None
    value_reference_id: int | None = None
    value_reference_display: str | None = None
    value_json: Any | None = None


class PlainTaskOutput(AuditFields):
    """Plain snake_case serialization of a Task output child row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="DB primary key of this output row.")
    type_text: str | None = None
    type_codings: list[PlainCodingRow] | None = None
    value_string: str | None = None
    value_boolean: bool | None = None
    value_integer: int | None = None
    value_decimal: float | None = None
    value_date: str | None = None
    value_date_time: str | None = None
    value_time: str | None = None
    value_uri: str | None = None
    value_code: str | None = None
    value_reference_reference: str | None = None
    value_reference: str | None = None
    value_reference_type: str | None = None
    value_reference_id: int | None = None
    value_reference_display: str | None = None
    value_json: Any | None = None
