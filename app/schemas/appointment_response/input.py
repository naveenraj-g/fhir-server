from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput
from app.schemas.enums import AppointmentResponseParticipantStatus, IdentifierUse

# ---------------------------------------------------------------------------
# Sub-resource list item schemas
# ---------------------------------------------------------------------------


class AppointmentResponseIdentifierInput(BaseModel):
    """identifier[] — mirrors
    app.schemas.appointment.input.AppointmentIdentifierInput."""

    model_config = ConfigDict(extra="forbid")
    use: IdentifierUse | None = Field(
        None,
        description="Identifies the purpose for this identifier, if known — usual|official|temp|secondary|old.",
    )
    type_coding: list[CodingInput] | None = Field(
        None, description="Coding(s) for this identifier's type."
    )
    type_text: str | None = Field(
        None, description="A human language representation of the identifier's type."
    )
    system: str | None = Field(None, description="Establishes the namespace for the value.")
    value: str | None = Field(
        None,
        description="The portion of the identifier typically relevant to the user and which is unique within the system.",
    )
    period_start: datetime | None = Field(
        None, description="Start of the time period during which this identifier is/was valid for use."
    )
    period_end: datetime | None = Field(
        None, description="End of the time period during which this identifier is/was valid for use."
    )
    assigner: str | None = Field(
        None,
        description="Organization that issued/manages this identifier, as a FHIR reference string (e.g. 'Organization/190001').",
    )
    assigner_display: str | None = Field(
        None, description="Plain text narrative that identifies the assigning organization in addition to the reference."
    )
    assigner_identifier_use: IdentifierUse | None = Field(
        None, description="Logical-identifier fallback for the assigner — identifies its purpose, if known."
    )
    assigner_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    assigner_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    assigner_identifier_type_code: str | None = Field(None, description="Fallback identifier — a symbol for its type.")
    assigner_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    assigner_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    assigner_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether its type was user-selected.")
    assigner_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    assigner_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    assigner_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — start of validity period.")
    assigner_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — end of validity period.")


class AppointmentResponseParticipantTypeInput(BaseModel):
    """One entry of participantType[] (0..* CodeableConcept) — role of
    participant in the appointment. One half of apr-1's "participantType.exists()
    or actor.exists()" — enforced by the FHIR validator, not Pydantic."""

    model_config = ConfigDict(extra="forbid")
    coding: list[CodingInput] | None = Field(None, description="Coding(s) for this participant role.")
    text: str | None = Field(None, description="A human language representation of the role.")


# ---------------------------------------------------------------------------
# Create / Patch
# ---------------------------------------------------------------------------


class AppointmentResponseCreateSchema(BaseModel):
    """Creates an AppointmentResponse and any combination of its
    sub-resource lists atomically in one request — same set-once-then-patch
    shape as Organization/.../Appointment, no separate scalar-only vs. full
    create split. tenant_id and created_by both come from the verified JWT
    (actor.org_id / actor.sub) — neither is a request body field. Like
    Organization/Location/.../Appointment, AppointmentResponse has no
    user_id field at all — it's a shared tenant-level entity, not scoped
    to an individual end-user.

    `actor` is polymorphic across 7 possible target types — see
    app.models.appointment_response.enums.AppointmentResponseActorReferenceType's
    docstring for which are modeled resources here.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "appointment": "Appointment/40001",
                "participant_status": "accepted",
                "actor": "Practitioner/30001",
                "comment": "Confirmed attendance",
                "identifier": [],
                "participant_type": [],
            }
        },
    )

    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries. Not yet validated against registered extension definitions.",
    )

    # appointment (1..1) Reference(Appointment) — required
    appointment: str = Field(
        ...,
        description="The appointment that this response is replying to, as a FHIR reference string (e.g. 'Appointment/40001'). Rejected with 422 if it doesn't exist in this org.",
    )
    appointment_display: str | None = Field(
        None, description="Plain text narrative that identifies the appointment in addition to the reference."
    )
    appointment_identifier_use: IdentifierUse | None = Field(
        None, description="Logical-identifier fallback for appointment — identifies its purpose, if known."
    )
    appointment_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    appointment_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    appointment_identifier_type_code: str | None = Field(None, description="Fallback identifier — a symbol for its type.")
    appointment_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    appointment_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    appointment_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether its type was user-selected.")
    appointment_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    appointment_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    appointment_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — start of validity period.")
    appointment_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — end of validity period.")

    start: datetime | None = Field(None, description="Date/Time this response was made.")
    end: datetime | None = Field(None, description="This may be either the same as the appointment start, or different.")

    # actor (0..1) Reference, polymorphic
    actor: str | None = Field(
        None,
        description="The Person, Location/HealthcareService or Device that this response is for, as a FHIR reference string (e.g. 'Practitioner/30001').",
    )
    actor_display: str | None = Field(
        None, description="Plain text narrative that identifies the actor in addition to the reference."
    )
    actor_identifier_use: IdentifierUse | None = Field(
        None, description="Logical-identifier fallback for the actor — identifies its purpose, if known."
    )
    actor_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    actor_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    actor_identifier_type_code: str | None = Field(None, description="Fallback identifier — a symbol for its type.")
    actor_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    actor_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    actor_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether its type was user-selected.")
    actor_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    actor_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    actor_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — start of validity period.")
    actor_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — end of validity period.")

    # participantStatus (1..1) — required
    participant_status: AppointmentResponseParticipantStatus = Field(
        ..., description="accepted | declined | tentative | needs-action."
    )

    comment: str | None = Field(
        None, description="Additional comments about the response."
    )

    identifier: list[AppointmentResponseIdentifierInput] | None = Field(
        None, description="External identifiers for this item."
    )
    participant_type: list[AppointmentResponseParticipantTypeInput] | None = Field(
        None, description="Role of participant in the appointment."
    )


class AppointmentResponsePatchSchema(BaseModel):
    """Partial update — only supplied fields are written. Every supplied
    sub-resource list (even `[]`) replaces the corresponding rows wholesale;
    omitted lists are left untouched. updated_by comes from the verified
    JWT (actor.sub), not a request body field."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "participant_status": "declined",
                "comment": "Can no longer attend",
            }
        },
    )

    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries — replaces the full list if supplied.",
    )
    appointment: str | None = Field(
        None, description="The appointment, as a FHIR reference string. Set to null to clear."
    )
    appointment_display: str | None = Field(None, description="Plain text narrative for the appointment.")
    appointment_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — its purpose, if known.")
    appointment_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    appointment_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    appointment_identifier_type_code: str | None = Field(None, description="Fallback identifier — a symbol for its type.")
    appointment_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    appointment_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    appointment_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether its type was user-selected.")
    appointment_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    appointment_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    appointment_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — start of validity period.")
    appointment_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — end of validity period.")

    start: datetime | None = Field(None, description="Date/Time this response was made.")
    end: datetime | None = Field(None, description="This may be either the same as the appointment start, or different.")

    actor: str | None = Field(None, description="The actor, as a FHIR reference string. Set to null to clear.")
    actor_display: str | None = Field(None, description="Plain text narrative for the actor.")
    actor_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — its purpose, if known.")
    actor_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    actor_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    actor_identifier_type_code: str | None = Field(None, description="Fallback identifier — a symbol for its type.")
    actor_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    actor_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    actor_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether its type was user-selected.")
    actor_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    actor_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    actor_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — start of validity period.")
    actor_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — end of validity period.")

    participant_status: AppointmentResponseParticipantStatus | None = Field(
        None, description="accepted | declined | tentative | needs-action."
    )
    comment: str | None = Field(None, description="Additional comments about the response.")

    identifier: list[AppointmentResponseIdentifierInput] | None = Field(
        None, description="External identifiers — replaces the full list if supplied."
    )
    participant_type: list[AppointmentResponseParticipantTypeInput] | None = Field(
        None, description="Role(s) of participant — replaces the full list if supplied."
    )
