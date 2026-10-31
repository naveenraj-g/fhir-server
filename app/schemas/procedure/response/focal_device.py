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
