from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class ScheduleActorInput(BaseModel):
    """Schedule.actor — the resource(s) this schedule resource is for
    (Reference(Patient|Practitioner|PractitionerRole|RelatedPerson|Device|
    HealthcareService|Location)). The reference string's own prefix (e.g.
    'Practitioner/30001' vs 'Location/230001') carries the target type —
    rejected with 422 if it names a modeled resource that doesn't exist in
    this org; Patient/RelatedPerson/Device aren't modeled resources in this
    system, so those rely on the identifier fallback fields below instead."""

    model_config = ConfigDict(extra="forbid")
    reference: str | None = Field(
        None,
        description="FHIR reference string to the actor, e.g. 'Practitioner/30001' or 'Location/230001'.",
    )
    reference_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the actor in addition to the reference.",
    )
    reference_identifier_use: IdentifierUse | None = Field(
        None,
        description="Logical-identifier fallback (used when there's no resolvable reference, e.g. a Patient/RelatedPerson/Device) — identifies the purpose for that identifier, if known.",
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
