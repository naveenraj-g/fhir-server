from pydantic import BaseModel, ConfigDict, Field

from app.schemas.procedure.response.codeable_concept import (
    PlainProcedureSingleConcept,
)


class FHIRProcedureFocalDevice(BaseModel):
    """FHIR R4 Procedure.focalDevice."""

    model_config = ConfigDict(extra="allow")

    action: dict | None = None
    manipulated: dict | None = None


class PlainProcedureFocalDevice(BaseModel):
    """Plain representation of ProcedureFocalDevice."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    action: PlainProcedureSingleConcept | None = None
    manipulated: str | None = None
    manipulated_display: str | None = None
    manipulated_identifier_use: str | None = None
    manipulated_identifier_type_system: str | None = None
    manipulated_identifier_type_version: str | None = None
    manipulated_identifier_type_code: str | None = None
    manipulated_identifier_type_display: str | None = None
    manipulated_identifier_type_text: str | None = None
    manipulated_identifier_type_user_selected: bool | None = None
    manipulated_identifier_system: str | None = None
    manipulated_identifier_value: str | None = None
    manipulated_identifier_period_start: str | None = None
    manipulated_identifier_period_end: str | None = None
