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
    actor_identifier_use: str | None = None
    actor_identifier_type_system: str | None = None
    actor_identifier_type_version: str | None = None
    actor_identifier_type_code: str | None = None
    actor_identifier_type_display: str | None = None
    actor_identifier_type_text: str | None = None
    actor_identifier_type_user_selected: bool | None = None
    actor_identifier_system: str | None = None
    actor_identifier_value: str | None = None
    actor_identifier_period_start: str | None = None
    actor_identifier_period_end: str | None = None

    on_behalf_of: str | None = None
    on_behalf_of_display: str | None = None
    on_behalf_of_identifier_use: str | None = None
    on_behalf_of_identifier_type_system: str | None = None
    on_behalf_of_identifier_type_version: str | None = None
    on_behalf_of_identifier_type_code: str | None = None
    on_behalf_of_identifier_type_display: str | None = None
    on_behalf_of_identifier_type_text: str | None = None
    on_behalf_of_identifier_type_user_selected: bool | None = None
    on_behalf_of_identifier_system: str | None = None
    on_behalf_of_identifier_value: str | None = None
    on_behalf_of_identifier_period_start: str | None = None
    on_behalf_of_identifier_period_end: str | None = None
