from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class ScheduleActorInput(BaseModel):
    """Schedule.actor — resource(s) that availability information is being
    provided for (Reference(Patient|Practitioner|PractitionerRole|
    RelatedPerson|Device|HealthcareService|Location)). Device isn't a modeled
    resource in this system, so a Device-typed reference gets no existence
    check and typically relies on the identifier fallback fields below."""

    model_config = ConfigDict(extra="forbid")
    reference: str | None = Field(
        None,
        description=(
            "FHIR reference string, e.g. 'Practitioner/30001'. Allowed types: "
            "Patient, Practitioner, PractitionerRole, RelatedPerson, Device, "
            "HealthcareService, Location — rejected with 422 if it doesn't "
            "resolve to an existing resource in this org (Device excepted, "
            "since it isn't a modeled resource here)."
        ),
    )
    reference_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the actor in addition to the reference.",
    )
    reference_identifier_use: IdentifierUse | None = Field(
        None,
        description="Logical-identifier fallback (used when there's no resolvable reference) — identifies the purpose for that identifier, if known.",
    )
    reference_identifier_type_system: str | None = Field(
        None,
        description="Fallback identifier — the code system that defines the meaning of its type code.",
    )
    reference_identifier_type_version: str | None = Field(
        None,
        description="Fallback identifier — the version of the code system used for its type code.",
    )
    reference_identifier_type_code: str | None = Field(
        None,
        description="Fallback identifier — a symbol in syntax defined by the code system.",
    )
    reference_identifier_type_display: str | None = Field(
        None,
        description="Fallback identifier — a representation of the meaning of its type code.",
    )
    reference_identifier_type_text: str | None = Field(
        None,
        description="Fallback identifier — a human language representation of its type.",
    )
    reference_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was chosen by a user directly.",
    )
    reference_identifier_system: str | None = Field(
        None, description="Fallback identifier — the namespace URL for the value."
    )
    reference_identifier_value: str | None = Field(
        None,
        description="Fallback identifier — the portion typically relevant to the user, unique within the system.",
    )
    reference_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of its validity period."
    )
    reference_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of its validity period."
    )
