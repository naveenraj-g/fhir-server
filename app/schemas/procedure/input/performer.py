from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.repository._reference_shared import _IDENTIFIER_FALLBACK_SUFFIXES
from app.schemas.enums import IdentifierUse
from app.schemas.procedure.input.codeable_concept import (
    ProcedureCodeableConceptInput,
)


class ProcedurePerformerInput(BaseModel):
    """Procedure.performer (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    function: ProcedureCodeableConceptInput | None = Field(
        None, description="Type of performance (e.g. primary surgeon, assistant)."
    )
    actor: str | None = Field(
        None,
        description="The reference to the practitioner, practitioner role, organization, patient, related person, or device (e.g. Practitioner/123).",
    )
    actor_display: str | None = Field(
        None, description="Plain text display for the actor reference."
    )
    actor_identifier_use: IdentifierUse | None = Field(None)
    actor_identifier_type_system: str | None = Field(None)
    actor_identifier_type_version: str | None = Field(None)
    actor_identifier_type_code: str | None = Field(None)
    actor_identifier_type_display: str | None = Field(None)
    actor_identifier_type_text: str | None = Field(None)
    actor_identifier_type_user_selected: bool | None = Field(None)
    actor_identifier_system: str | None = Field(None)
    actor_identifier_value: str | None = Field(None)
    actor_identifier_period_start: datetime | None = Field(None)
    actor_identifier_period_end: datetime | None = Field(None)

    on_behalf_of: str | None = Field(
        None,
        description="Organization the device or practitioner was acting for (e.g. Organization/123).",
    )
    on_behalf_of_display: str | None = Field(
        None, description="Plain text display for the on_behalf_of reference."
    )
    on_behalf_of_identifier_use: IdentifierUse | None = Field(None)
    on_behalf_of_identifier_type_system: str | None = Field(None)
    on_behalf_of_identifier_type_version: str | None = Field(None)
    on_behalf_of_identifier_type_code: str | None = Field(None)
    on_behalf_of_identifier_type_display: str | None = Field(None)
    on_behalf_of_identifier_type_text: str | None = Field(None)
    on_behalf_of_identifier_type_user_selected: bool | None = Field(None)
    on_behalf_of_identifier_system: str | None = Field(None)
    on_behalf_of_identifier_value: str | None = Field(None)
    on_behalf_of_identifier_period_start: datetime | None = Field(None)
    on_behalf_of_identifier_period_end: datetime | None = Field(None)

    @model_validator(mode="after")
    def validate_actor(self) -> "ProcedurePerformerInput":
        has_ref = bool(self.actor)
        has_ident = any(
            getattr(self, f"actor_{suffix}") is not None
            for suffix in _IDENTIFIER_FALLBACK_SUFFIXES
        )
        has_disp = bool(self.actor_display)
        if not (has_ref or has_ident or has_disp):
            raise ValueError(
                "performer.actor: at least one of actor reference string, actor display, or actor_identifier_* fallback must be provided."
            )
        return self
