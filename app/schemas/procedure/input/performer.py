from pydantic import BaseModel, ConfigDict, Field

from app.schemas.procedure.input.codeable_concept import (
    ProcedureCodeableConceptInput,
)


class ProcedurePerformerInput(BaseModel):
    """Procedure.performer (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    function: ProcedureCodeableConceptInput | None = Field(
        None, description="Type of performance (e.g. primary surgeon, assistant)."
    )
    actor: str = Field(
        ...,
        description="The reference to the practitioner, practitioner role, organization, patient, related person, or device (e.g. Practitioner/123).",
    )
    actor_display: str | None = Field(
        None, description="Plain text display for the actor reference."
    )
    on_behalf_of: str | None = Field(
        None,
        description="Organization the device or practitioner was acting for (e.g. Organization/123).",
    )
    on_behalf_of_display: str | None = Field(
        None, description="Plain text display for the on_behalf_of reference."
    )
