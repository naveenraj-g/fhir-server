from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.repository._reference_shared import _IDENTIFIER_FALLBACK_SUFFIXES
from app.schemas.enums import IdentifierUse
from app.schemas.procedure.input.codeable_concept import (
    ProcedureCodeableConceptInput,
)


class ProcedureFocalDeviceInput(BaseModel):
    """Procedure.focalDevice (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    action: ProcedureCodeableConceptInput | None = Field(
        None, description="Kind of change to device (implanted, removed, etc.)."
    )
    manipulated: str | None = Field(
        None,
        description="Device that was changed or manipulated (e.g. Device/123).",
    )
    manipulated_display: str | None = Field(
        None, description="Plain text display for the manipulated device reference."
    )
    manipulated_identifier_use: IdentifierUse | None = Field(None)
    manipulated_identifier_type_system: str | None = Field(None)
    manipulated_identifier_type_version: str | None = Field(None)
    manipulated_identifier_type_code: str | None = Field(None)
    manipulated_identifier_type_display: str | None = Field(None)
    manipulated_identifier_type_text: str | None = Field(None)
    manipulated_identifier_type_user_selected: bool | None = Field(None)
    manipulated_identifier_system: str | None = Field(None)
    manipulated_identifier_value: str | None = Field(None)
    manipulated_identifier_period_start: datetime | None = Field(None)
    manipulated_identifier_period_end: datetime | None = Field(None)

    @model_validator(mode="after")
    def validate_manipulated(self) -> "ProcedureFocalDeviceInput":
        has_ref = bool(self.manipulated)
        has_ident = any(
            getattr(self, f"manipulated_{suffix}") is not None
            for suffix in _IDENTIFIER_FALLBACK_SUFFIXES
        )
        has_disp = bool(self.manipulated_display)
        if not (has_ref or has_ident or has_disp):
            raise ValueError(
                "focal_device.manipulated: at least one of manipulated reference string, manipulated display, or manipulated_identifier_* fallback must be provided."
            )
        return self
