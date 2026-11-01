from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import EpisodeOfCareStatus, IdentifierUse
from app.schemas.episode_of_care.input.codeable_concept import (
    EpisodeOfCareCodeableConceptInput,
)
from app.schemas.episode_of_care.input.diagnosis import EpisodeOfCareDiagnosisInput
from app.schemas.episode_of_care.input.identifier import EpisodeOfCareIdentifierInput
from app.schemas.episode_of_care.input.reference import EpisodeOfCareReferenceInput
from app.schemas.episode_of_care.input.status_history import (
    EpisodeOfCareStatusHistoryInput,
)


class EpisodeOfCareCreateSchema(BaseModel):
    """Request payload for POST /api/fhir/v1/episodes-of-care/."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "active",
                "patient": "Patient/10001",
                "patient_display": "Jane Doe",
                "managing_organization": "Organization/190001",
                "managing_organization_display": "Acme Health System",
                "period_start": "2026-01-01T00:00:00Z",
                "period_end": "2026-12-31T23:59:59Z",
                "care_manager": "Practitioner/30001",
                "care_manager_display": "Dr. Adam Careful",
                "type": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/episodeofcare-type",
                                "code": "hacc",
                                "display": "Home and Community Care",
                            }
                        ],
                        "text": "Home and Community Care",
                    }
                ],
                "diagnosis": [
                    {
                        "condition": "Condition/120001",
                        "condition_display": "Chronic Heart Failure",
                        "rank": 1,
                    }
                ],
                "team": ["CareTeam/390001"],
            }
        },
    )

    status: EpisodeOfCareStatus = Field(
        EpisodeOfCareStatus.active,
        description="planned | waitlist | active | onhold | finished | cancelled | entered-in-error",
    )
    status_history: list[EpisodeOfCareStatusHistoryInput] | None = Field(
        None, description="Past list of status codes (and reasons) for the status of the episode."
    )
    type: list[EpisodeOfCareCodeableConceptInput] | None = Field(
        None, description="Type/flavor - e.g. specialist referral, disease management."
    )
    diagnosis: list[EpisodeOfCareDiagnosisInput] | None = Field(
        None, description="The list of diagnosis relevant to this episode of care."
    )
    patient: str | None = Field(
        None, description="The patient who is the focus of this episode of care (Reference(Patient))."
    )
    patient_display: str | None = Field(None, description="Display name for patient.")
    patient_identifier_use: IdentifierUse | None = Field(None, description="Patient identifier use.")
    patient_identifier_type_system: str | None = Field(None, description="Patient identifier type system.")
    patient_identifier_type_version: str | None = Field(None, description="Patient identifier type version.")
    patient_identifier_type_code: str | None = Field(None, description="Patient identifier type code.")
    patient_identifier_type_display: str | None = Field(None, description="Patient identifier type display.")
    patient_identifier_type_user_selected: bool | None = Field(
        None, description="Patient identifier type user selected."
    )
    patient_identifier_type_text: str | None = Field(None, description="Patient identifier type text.")
    patient_identifier_system: str | None = Field(None, description="Patient identifier system.")
    patient_identifier_value: str | None = Field(None, description="Patient identifier value.")
    patient_identifier_period_start: datetime | None = Field(
        None, description="Patient identifier period start."
    )
    patient_identifier_period_end: datetime | None = Field(
        None, description="Patient identifier period end."
    )

    managing_organization: str | None = Field(
        None, description="Organization that assumes responsibility for care (Reference(Organization))."
    )
    managing_organization_display: str | None = Field(
        None, description="Display name for managing organization."
    )
    managing_organization_identifier_use: IdentifierUse | None = Field(
        None, description="Managing organization identifier use."
    )
    managing_organization_identifier_type_system: str | None = Field(
        None, description="Managing organization identifier type system."
    )
    managing_organization_identifier_type_version: str | None = Field(
        None, description="Managing organization identifier type version."
    )
    managing_organization_identifier_type_code: str | None = Field(
        None, description="Managing organization identifier type code."
    )
    managing_organization_identifier_type_display: str | None = Field(
        None, description="Managing organization identifier type display."
    )
    managing_organization_identifier_type_user_selected: bool | None = Field(
        None, description="Managing organization identifier type user selected."
    )
    managing_organization_identifier_type_text: str | None = Field(
        None, description="Managing organization identifier type text."
    )
    managing_organization_identifier_system: str | None = Field(
        None, description="Managing organization identifier system."
    )
    managing_organization_identifier_value: str | None = Field(
        None, description="Managing organization identifier value."
    )
    managing_organization_identifier_period_start: datetime | None = Field(
        None, description="Managing organization identifier period start."
    )
    managing_organization_identifier_period_end: datetime | None = Field(
        None, description="Managing organization identifier period end."
    )

    period_start: datetime | None = Field(None, description="Interval during responsibility is assumed.")
    period_end: datetime | None = Field(None, description="Interval during responsibility is assumed.")
    referral_request: list[EpisodeOfCareReferenceInput | str] | None = Field(
        None, description="Originating Referral Request(s) (Reference(ServiceRequest))."
    )
    care_manager: str | None = Field(
        None, description="Care manager/care coordinator for the patient (Reference(Practitioner | PractitionerRole))."
    )
    care_manager_display: str | None = Field(None, description="Display name for care manager.")
    care_manager_identifier_use: IdentifierUse | None = Field(None, description="Care manager identifier use.")
    care_manager_identifier_type_system: str | None = Field(
        None, description="Care manager identifier type system."
    )
    care_manager_identifier_type_version: str | None = Field(
        None, description="Care manager identifier type version."
    )
    care_manager_identifier_type_code: str | None = Field(None, description="Care manager identifier type code.")
    care_manager_identifier_type_display: str | None = Field(
        None, description="Care manager identifier type display."
    )
    care_manager_identifier_type_user_selected: bool | None = Field(
        None, description="Care manager identifier type user selected."
    )
    care_manager_identifier_type_text: str | None = Field(
        None, description="Care manager identifier type text."
    )
    care_manager_identifier_system: str | None = Field(None, description="Care manager identifier system.")
    care_manager_identifier_value: str | None = Field(None, description="Care manager identifier value.")
    care_manager_identifier_period_start: datetime | None = Field(
        None, description="Care manager identifier period start."
    )
    care_manager_identifier_period_end: datetime | None = Field(
        None, description="Care manager identifier period end."
    )

    team: list[EpisodeOfCareReferenceInput | str] | None = Field(
        None, description="Other practitioners facilitating this episode of care (Reference(CareTeam))."
    )
    account: list[EpisodeOfCareReferenceInput | str] | None = Field(
        None, description="The set of accounts that may be used for billing for this EpisodeOfCare (Reference(Account))."
    )
    identifier: list[EpisodeOfCareIdentifierInput] | None = Field(
        None, description="Business Identifier(s) relevant for this EpisodeOfCare."
    )


class EpisodeOfCarePatchSchema(BaseModel):
    """Request payload for PATCH /api/fhir/v1/episodes-of-care/{episode_of_care_id}."""

    model_config = ConfigDict(extra="forbid")

    status: EpisodeOfCareStatus | None = Field(
        None,
        description="planned | waitlist | active | onhold | finished | cancelled | entered-in-error",
    )
    status_history: list[EpisodeOfCareStatusHistoryInput] | None = Field(
        None, description="Past list of status codes (and reasons) for the status of the episode."
    )
    type: list[EpisodeOfCareCodeableConceptInput] | None = Field(
        None, description="Type/flavor - e.g. specialist referral, disease management."
    )
    diagnosis: list[EpisodeOfCareDiagnosisInput] | None = Field(
        None, description="The list of diagnosis relevant to this episode of care."
    )
    patient: str | None = Field(
        None, description="The patient who is the focus of this episode of care (Reference(Patient))."
    )
    patient_display: str | None = Field(None, description="Display name for patient.")
    patient_identifier_use: IdentifierUse | None = Field(None, description="Patient identifier use.")
    patient_identifier_type_system: str | None = Field(None, description="Patient identifier type system.")
    patient_identifier_type_version: str | None = Field(None, description="Patient identifier type version.")
    patient_identifier_type_code: str | None = Field(None, description="Patient identifier type code.")
    patient_identifier_type_display: str | None = Field(None, description="Patient identifier type display.")
    patient_identifier_type_user_selected: bool | None = Field(
        None, description="Patient identifier type user selected."
    )
    patient_identifier_type_text: str | None = Field(None, description="Patient identifier type text.")
    patient_identifier_system: str | None = Field(None, description="Patient identifier system.")
    patient_identifier_value: str | None = Field(None, description="Patient identifier value.")
    patient_identifier_period_start: datetime | None = Field(
        None, description="Patient identifier period start."
    )
    patient_identifier_period_end: datetime | None = Field(
        None, description="Patient identifier period end."
    )

    managing_organization: str | None = Field(
        None, description="Organization that assumes responsibility for care (Reference(Organization))."
    )
    managing_organization_display: str | None = Field(
        None, description="Display name for managing organization."
    )
    managing_organization_identifier_use: IdentifierUse | None = Field(
        None, description="Managing organization identifier use."
    )
    managing_organization_identifier_type_system: str | None = Field(
        None, description="Managing organization identifier type system."
    )
    managing_organization_identifier_type_version: str | None = Field(
        None, description="Managing organization identifier type version."
    )
    managing_organization_identifier_type_code: str | None = Field(
        None, description="Managing organization identifier type code."
    )
    managing_organization_identifier_type_display: str | None = Field(
        None, description="Managing organization identifier type display."
    )
    managing_organization_identifier_type_user_selected: bool | None = Field(
        None, description="Managing organization identifier type user selected."
    )
    managing_organization_identifier_type_text: str | None = Field(
        None, description="Managing organization identifier type text."
    )
    managing_organization_identifier_system: str | None = Field(
        None, description="Managing organization identifier system."
    )
    managing_organization_identifier_value: str | None = Field(
        None, description="Managing organization identifier value."
    )
    managing_organization_identifier_period_start: datetime | None = Field(
        None, description="Managing organization identifier period start."
    )
    managing_organization_identifier_period_end: datetime | None = Field(
        None, description="Managing organization identifier period end."
    )

    period_start: datetime | None = Field(None, description="Interval during responsibility is assumed.")
    period_end: datetime | None = Field(None, description="Interval during responsibility is assumed.")
    referral_request: list[EpisodeOfCareReferenceInput | str] | None = Field(
        None, description="Originating Referral Request(s) (Reference(ServiceRequest))."
    )
    care_manager: str | None = Field(
        None, description="Care manager/care coordinator for the patient (Reference(Practitioner | PractitionerRole))."
    )
    care_manager_display: str | None = Field(None, description="Display name for care manager.")
    care_manager_identifier_use: IdentifierUse | None = Field(None, description="Care manager identifier use.")
    care_manager_identifier_type_system: str | None = Field(
        None, description="Care manager identifier type system."
    )
    care_manager_identifier_type_version: str | None = Field(
        None, description="Care manager identifier type version."
    )
    care_manager_identifier_type_code: str | None = Field(None, description="Care manager identifier type code.")
    care_manager_identifier_type_display: str | None = Field(
        None, description="Care manager identifier type display."
    )
    care_manager_identifier_type_user_selected: bool | None = Field(
        None, description="Care manager identifier type user selected."
    )
    care_manager_identifier_type_text: str | None = Field(
        None, description="Care manager identifier type text."
    )
    care_manager_identifier_system: str | None = Field(None, description="Care manager identifier system.")
    care_manager_identifier_value: str | None = Field(None, description="Care manager identifier value.")
    care_manager_identifier_period_start: datetime | None = Field(
        None, description="Care manager identifier period start."
    )
    care_manager_identifier_period_end: datetime | None = Field(
        None, description="Care manager identifier period end."
    )

    team: list[EpisodeOfCareReferenceInput | str] | None = Field(
        None, description="Other practitioners facilitating this episode of care (Reference(CareTeam))."
    )
    account: list[EpisodeOfCareReferenceInput | str] | None = Field(
        None, description="The set of accounts that may be used for billing for this EpisodeOfCare (Reference(Account))."
    )
    identifier: list[EpisodeOfCareIdentifierInput] | None = Field(
        None, description="Business Identifier(s) relevant for this EpisodeOfCare."
    )
