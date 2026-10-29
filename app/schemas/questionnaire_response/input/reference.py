from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse

# ---------------------------------------------------------------------------
# Shared field-group shapes for every bare-Reference field on
# QuestionnaireResponse — mirrors app.schemas.appointment.input._ReferenceListInput
# (for 0..* list fields) and the single-0..1-field pattern used by
# app.schemas.schedule.input.actor.ScheduleActorInput, just duplicated
# locally per this codebase's convention of not sharing resource-specific
# private schema classes across resource packages.
# ---------------------------------------------------------------------------


class _ReferenceListInput(BaseModel):
    """Shared shape for basedOn[]/partOf[] — both are bare 0..* Reference
    lists, so the field prefix is `reference` (not e.g. `actor`), since the
    whole object IS the reference."""

    model_config = ConfigDict(extra="forbid")
    reference: str | None = Field(None, description="FHIR reference string, e.g. 'ServiceRequest/123'.")
    reference_display: str | None = Field(
        None, description="Plain text narrative that identifies the target in addition to the reference."
    )
    reference_identifier_use: IdentifierUse | None = Field(
        None, description="Logical-identifier fallback (used when there's no resolvable reference) — identifies its purpose, if known."
    )
    reference_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    reference_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    reference_identifier_type_code: str | None = Field(None, description="Fallback identifier — a symbol for its type.")
    reference_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    reference_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    reference_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether its type was user-selected.")
    reference_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    reference_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    reference_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — start of validity period.")
    reference_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — end of validity period.")


class QuestionnaireResponseBasedOnInput(_ReferenceListInput):
    """basedOn[] — Reference(CarePlan|ServiceRequest). Neither is a modeled
    resource in this system — see
    app.models.questionnaire_response.enums.QuestionnaireResponseBasedOnReferenceType's
    docstring."""


class QuestionnaireResponsePartOfInput(_ReferenceListInput):
    """partOf[] — Reference(Observation|Procedure). Neither is a modeled
    resource in this system."""


class _SingleReferenceInput(BaseModel):
    """Shared shape for subject/author/source/encounter — each a bare 0..1
    Reference field, same field group as `_ReferenceListInput` above but
    used as a single nested object rather than a list item."""

    model_config = ConfigDict(extra="forbid")
    reference: str | None = Field(None, description="FHIR reference string, e.g. 'Practitioner/30001'.")
    reference_display: str | None = Field(
        None, description="Plain text narrative that identifies the target in addition to the reference."
    )
    reference_identifier_use: IdentifierUse | None = Field(
        None, description="Logical-identifier fallback (used when there's no resolvable reference) — identifies its purpose, if known."
    )
    reference_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    reference_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    reference_identifier_type_code: str | None = Field(None, description="Fallback identifier — a symbol for its type.")
    reference_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    reference_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    reference_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether its type was user-selected.")
    reference_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    reference_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    reference_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — start of validity period.")
    reference_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — end of validity period.")


class QuestionnaireResponseSubjectInput(_SingleReferenceInput):
    """subject (0..1) — Reference(Any). Target type is never validated
    against an enum — see
    app.models.questionnaire_response.core.QuestionnaireResponseModel's
    docstring."""


class QuestionnaireResponseEncounterInput(_SingleReferenceInput):
    """encounter (0..1) — Reference(Encounter). Encounter IS a modeled
    resource; rejected with 422 if it doesn't exist in this org."""


class QuestionnaireResponseAuthorInput(_SingleReferenceInput):
    """author (0..1) — Reference(Device|Practitioner|PractitionerRole|
    Patient|RelatedPerson|Organization). Only Practitioner/
    PractitionerRole/Organization are modeled resources here."""


class QuestionnaireResponseSourceInput(_SingleReferenceInput):
    """source (0..1) — Reference(Patient|Practitioner|PractitionerRole|
    RelatedPerson). Only Practitioner/PractitionerRole are modeled
    resources here."""
