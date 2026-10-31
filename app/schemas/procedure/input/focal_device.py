from pydantic import BaseModel, ConfigDict, Field

from app.schemas.procedure.input.codeable_concept import (
    ProcedureCodeableConceptInput,
)


class ProcedureFocalDeviceInput(BaseModel):
    """Procedure.focalDevice (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    action: ProcedureCodeableConceptInput | None = Field(
        None, description="Kind of change to device (implanted, removed, etc.)."
    )
    manipulated: str = Field(
        ...,
        description="Device that was changed or manipulated (e.g. Device/123).",
    )
    manipulated_display: str | None = Field(
        None, description="Plain text display for the manipulated device reference."
    )
