from pydantic import BaseModel, ConfigDict, Field

from app.schemas.procedure.response.codeable_concept import (
    PlainProcedureSingleConcept,
)


class FHIRProcedurePerformer(BaseModel):
    """FHIR R4 Procedure.performer."""

    model_config = ConfigDict(extra="allow")

    function: dict | None = None
    actor: dict | None = None
    onBehalfOf: dict | None = None


class PlainProcedurePerformer(BaseModel):
    """Plain representation of ProcedurePerformer."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    function: PlainProcedureSingleConcept | None = None
    actor: str | None = None
    actor_display: str | None = None
    on_behalf_of: str | None = None
    on_behalf_of_display: str | None = None
