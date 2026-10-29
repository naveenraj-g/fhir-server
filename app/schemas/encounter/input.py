from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput
from app.schemas.enums import (
    EncounterLengthComparator,
    EncounterLocationStatus,
    EncounterStatus,
    IdentifierUse,
)

# ---------------------------------------------------------------------------
# Shared reference-list shape (reasonReference/episodeOfCare/basedOn/
# appointment/account/diagnosis.condition/participant.individual/location.
# location/hospitalization.origin/destination all use this same
# reference/display/identifier-fallback shape, just under different field
# prefixes) — mirrors app.schemas.appointment.input's own per-field
# duplicates of this shape.
# ---------------------------------------------------------------------------


class EncounterIdentifierInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: IdentifierUse | None = None
    type_coding: list[CodingInput] | None = None
    type_text: str | None = None
    system: str | None = None
    value: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    assigner: str | None = Field(None, description="Reference string, e.g. 'Organization/190001'.")
    assigner_display: str | None = None
    assigner_identifier_use: IdentifierUse | None = None
    assigner_identifier_type_system: str | None = None
    assigner_identifier_type_version: str | None = None
    assigner_identifier_type_code: str | None = None
    assigner_identifier_type_display: str | None = None
    assigner_identifier_type_text: str | None = None
    assigner_identifier_type_user_selected: bool | None = None
    assigner_identifier_system: str | None = None
    assigner_identifier_value: str | None = None
    assigner_identifier_period_start: datetime | None = None
    assigner_identifier_period_end: datetime | None = None


class EncounterStatusHistoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: EncounterStatus = Field(..., description="planned|arrived|triaged|in-progress|onleave|finished|cancelled|entered-in-error|unknown.")
    period_start: datetime | None = None
    period_end: datetime | None = None


class EncounterClassHistoryInput(BaseModel):
    """classHistory[] entry. `class_coding` is a single Coding (not a
    list) — Encounter.classHistory.class, like Encounter.class itself, is
    type Coding, not CodeableConcept."""

    model_config = ConfigDict(extra="forbid")
    class_coding: CodingInput | None = Field(None, description="The Coding for this historical class.")
    period_start: datetime | None = None
    period_end: datetime | None = None


class _CodeableConceptListInput(BaseModel):
    """Shared shape for every 0..* CodeableConcept list field on
    Encounter (type/reasonCode/participant.type/diagnosis.use-as-single/
    hospitalization.dietPreference/specialCourtesy/specialArrangement)."""

    model_config = ConfigDict(extra="forbid")
    coding: list[CodingInput] | None = None
    text: str | None = None


class EncounterTypeInput(_CodeableConceptListInput):
    """type[] — specific type of encounter."""


class EncounterReasonCodeInput(_CodeableConceptListInput):
    """reasonCode[] — coded reason the encounter takes place."""


class EncounterParticipantTypeInput(_CodeableConceptListInput):
    """One entry of participant.type[]."""


class EncounterHospitalizationDietPreferenceInput(_CodeableConceptListInput):
    """One entry of hospitalization.dietPreference[]."""


class EncounterHospitalizationSpecialCourtesyInput(_CodeableConceptListInput):
    """One entry of hospitalization.specialCourtesy[]."""


class EncounterHospitalizationSpecialArrangementInput(_CodeableConceptListInput):
    """One entry of hospitalization.specialArrangement[]."""


class _ReferenceListInput(BaseModel):
    """Shared shape for every 0..* bare-Reference list field on Encounter
    (episodeOfCare/basedOn/appointment/reasonReference/account) — the
    field prefix is `reference`, since the whole object IS the
    reference. Mirrors app.schemas.appointment.input's own
    `_ReferenceListInput`."""

    model_config = ConfigDict(extra="forbid")
    reference: str | None = Field(None, description="FHIR reference string, e.g. 'Appointment/40001'.")
    reference_display: str | None = None
    reference_identifier_use: IdentifierUse | None = None
    reference_identifier_type_system: str | None = None
    reference_identifier_type_version: str | None = None
    reference_identifier_type_code: str | None = None
    reference_identifier_type_display: str | None = None
    reference_identifier_type_text: str | None = None
    reference_identifier_type_user_selected: bool | None = None
    reference_identifier_system: str | None = None
    reference_identifier_value: str | None = None
    reference_identifier_period_start: datetime | None = None
    reference_identifier_period_end: datetime | None = None


class EncounterEpisodeOfCareInput(_ReferenceListInput):
    """episodeOfCare[] — Reference(EpisodeOfCare). Not a modeled resource here."""


class EncounterBasedOnInput(_ReferenceListInput):
    """basedOn[] — Reference(ServiceRequest). Not a modeled resource here."""


class EncounterAppointmentInput(_ReferenceListInput):
    """appointment[] — Reference(Appointment). Appointment IS modeled; rejected with 422 if it doesn't exist in this org."""


class EncounterReasonReferenceInput(_ReferenceListInput):
    """reasonReference[] — Reference(Condition|Procedure|Observation|ImmunizationRecommendation). None modeled here."""


class EncounterAccountInput(_ReferenceListInput):
    """account[] — Reference(Account). Not a modeled resource here."""


class EncounterParticipantInput(BaseModel):
    """participant[] — participants involved in the encounter."""

    model_config = ConfigDict(extra="forbid")
    type: list[EncounterParticipantTypeInput] | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    individual: str | None = Field(
        None, description="Reference(Practitioner|PractitionerRole|RelatedPerson), e.g. 'Practitioner/30001'."
    )
    individual_display: str | None = None
    individual_identifier_use: IdentifierUse | None = None
    individual_identifier_type_system: str | None = None
    individual_identifier_type_version: str | None = None
    individual_identifier_type_code: str | None = None
    individual_identifier_type_display: str | None = None
    individual_identifier_type_text: str | None = None
    individual_identifier_type_user_selected: bool | None = None
    individual_identifier_system: str | None = None
    individual_identifier_value: str | None = None
    individual_identifier_period_start: datetime | None = None
    individual_identifier_period_end: datetime | None = None


class EncounterDiagnosisInput(BaseModel):
    """diagnosis[] — the list of diagnosis relevant to this encounter."""

    model_config = ConfigDict(extra="forbid")
    condition: str | None = Field(
        None, description="Reference(Condition|Procedure), required per spec. Neither modeled here."
    )
    condition_display: str | None = None
    condition_identifier_use: IdentifierUse | None = None
    condition_identifier_type_system: str | None = None
    condition_identifier_type_version: str | None = None
    condition_identifier_type_code: str | None = None
    condition_identifier_type_display: str | None = None
    condition_identifier_type_text: str | None = None
    condition_identifier_type_user_selected: bool | None = None
    condition_identifier_system: str | None = None
    condition_identifier_value: str | None = None
    condition_identifier_period_start: datetime | None = None
    condition_identifier_period_end: datetime | None = None
    use_coding: list[CodingInput] | None = None
    use_text: str | None = None
    rank: int | None = Field(None, gt=0)


class EncounterHospitalizationInput(BaseModel):
    """hospitalization (0..1) — details about the admission to a
    healthcare service."""

    model_config = ConfigDict(extra="forbid")

    pre_admission_identifier_use: IdentifierUse | None = None
    pre_admission_identifier_type_coding: list[CodingInput] | None = None
    pre_admission_identifier_type_text: str | None = None
    pre_admission_identifier_system: str | None = None
    pre_admission_identifier_value: str | None = None
    pre_admission_identifier_period_start: datetime | None = None
    pre_admission_identifier_period_end: datetime | None = None
    pre_admission_identifier_assigner: str | None = None
    pre_admission_identifier_assigner_display: str | None = None
    pre_admission_identifier_assigner_identifier_use: IdentifierUse | None = None
    pre_admission_identifier_assigner_identifier_type_system: str | None = None
    pre_admission_identifier_assigner_identifier_type_version: str | None = None
    pre_admission_identifier_assigner_identifier_type_code: str | None = None
    pre_admission_identifier_assigner_identifier_type_display: str | None = None
    pre_admission_identifier_assigner_identifier_type_text: str | None = None
    pre_admission_identifier_assigner_identifier_type_user_selected: bool | None = None
    pre_admission_identifier_assigner_identifier_system: str | None = None
    pre_admission_identifier_assigner_identifier_value: str | None = None
    pre_admission_identifier_assigner_identifier_period_start: datetime | None = None
    pre_admission_identifier_assigner_identifier_period_end: datetime | None = None

    origin: str | None = Field(None, description="Reference(Location|Organization). Both modeled; validated.")
    origin_display: str | None = None
    origin_identifier_use: IdentifierUse | None = None
    origin_identifier_type_system: str | None = None
    origin_identifier_type_version: str | None = None
    origin_identifier_type_code: str | None = None
    origin_identifier_type_display: str | None = None
    origin_identifier_type_text: str | None = None
    origin_identifier_type_user_selected: bool | None = None
    origin_identifier_system: str | None = None
    origin_identifier_value: str | None = None
    origin_identifier_period_start: datetime | None = None
    origin_identifier_period_end: datetime | None = None

    admit_source_coding: list[CodingInput] | None = None
    admit_source_text: str | None = None
    re_admission_coding: list[CodingInput] | None = None
    re_admission_text: str | None = None
    diet_preference: list[EncounterHospitalizationDietPreferenceInput] | None = None
    special_courtesy: list[EncounterHospitalizationSpecialCourtesyInput] | None = None
    special_arrangement: list[EncounterHospitalizationSpecialArrangementInput] | None = None

    destination: str | None = Field(None, description="Reference(Location|Organization). Both modeled; validated.")
    destination_display: str | None = None
    destination_identifier_use: IdentifierUse | None = None
    destination_identifier_type_system: str | None = None
    destination_identifier_type_version: str | None = None
    destination_identifier_type_code: str | None = None
    destination_identifier_type_display: str | None = None
    destination_identifier_type_text: str | None = None
    destination_identifier_type_user_selected: bool | None = None
    destination_identifier_system: str | None = None
    destination_identifier_value: str | None = None
    destination_identifier_period_start: datetime | None = None
    destination_identifier_period_end: datetime | None = None

    discharge_disposition_coding: list[CodingInput] | None = None
    discharge_disposition_text: str | None = None


class EncounterLocationInput(BaseModel):
    """location[] — list of locations where the patient has been during this encounter."""

    model_config = ConfigDict(extra="forbid")
    location: str | None = Field(None, description="Reference(Location), required per spec. Location IS modeled; validated.")
    location_display: str | None = None
    location_identifier_use: IdentifierUse | None = None
    location_identifier_type_system: str | None = None
    location_identifier_type_version: str | None = None
    location_identifier_type_code: str | None = None
    location_identifier_type_display: str | None = None
    location_identifier_type_text: str | None = None
    location_identifier_type_user_selected: bool | None = None
    location_identifier_system: str | None = None
    location_identifier_value: str | None = None
    location_identifier_period_start: datetime | None = None
    location_identifier_period_end: datetime | None = None
    status: EncounterLocationStatus | None = None
    physical_type_coding: list[CodingInput] | None = None
    physical_type_text: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None


# ---------------------------------------------------------------------------
# Create / Patch
# ---------------------------------------------------------------------------


class EncounterCreateSchema(BaseModel):
    """Creates an Encounter and any combination of its sub-resource lists
    atomically in one request — same set-once-then-patch shape as every
    other auth-rollout resource. tenant_id and created_by both come from
    the verified JWT; neither is a request body field. Encounter has no
    user_id field — it's a shared tenant-level entity."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "in_progress",
                "class_coding": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB", "display": "ambulatory"},
                "subject": "Patient/999",
                "period_start": "2026-02-01T09:00:00Z",
                "participant": [{"individual": "Practitioner/30001"}],
            }
        },
    )

    extension: list[dict] | None = None

    status: EncounterStatus = Field(..., description="planned|arrived|triaged|in-progress|onleave|finished|cancelled|entered-in-error|unknown.")
    class_coding: CodingInput = Field(..., description="The Coding for Encounter.class (1..1, not CodeableConcept).")

    service_type_coding: list[CodingInput] | None = None
    service_type_text: str | None = None
    priority_coding: list[CodingInput] | None = None
    priority_text: str | None = None

    subject: str | None = Field(None, description="Reference(Patient|Group). Neither modeled here.")
    subject_display: str | None = None
    subject_identifier_use: IdentifierUse | None = None
    subject_identifier_type_system: str | None = None
    subject_identifier_type_version: str | None = None
    subject_identifier_type_code: str | None = None
    subject_identifier_type_display: str | None = None
    subject_identifier_type_text: str | None = None
    subject_identifier_type_user_selected: bool | None = None
    subject_identifier_system: str | None = None
    subject_identifier_value: str | None = None
    subject_identifier_period_start: datetime | None = None
    subject_identifier_period_end: datetime | None = None

    period_start: datetime | None = None
    period_end: datetime | None = None

    length_value: Decimal | None = None
    length_comparator: EncounterLengthComparator | None = None
    length_unit: str | None = None
    length_system: str | None = None
    length_code: str | None = None

    service_provider: str | None = Field(None, description="Reference(Organization). Organization IS modeled; validated.")
    service_provider_display: str | None = None
    service_provider_identifier_use: IdentifierUse | None = None
    service_provider_identifier_type_system: str | None = None
    service_provider_identifier_type_version: str | None = None
    service_provider_identifier_type_code: str | None = None
    service_provider_identifier_type_display: str | None = None
    service_provider_identifier_type_text: str | None = None
    service_provider_identifier_type_user_selected: bool | None = None
    service_provider_identifier_system: str | None = None
    service_provider_identifier_value: str | None = None
    service_provider_identifier_period_start: datetime | None = None
    service_provider_identifier_period_end: datetime | None = None

    part_of: str | None = Field(None, description="Reference(Encounter), self-referential. Rejected with 422 if it doesn't exist in this org.")
    part_of_display: str | None = None
    part_of_identifier_use: IdentifierUse | None = None
    part_of_identifier_type_system: str | None = None
    part_of_identifier_type_version: str | None = None
    part_of_identifier_type_code: str | None = None
    part_of_identifier_type_display: str | None = None
    part_of_identifier_type_text: str | None = None
    part_of_identifier_type_user_selected: bool | None = None
    part_of_identifier_system: str | None = None
    part_of_identifier_value: str | None = None
    part_of_identifier_period_start: datetime | None = None
    part_of_identifier_period_end: datetime | None = None

    identifier: list[EncounterIdentifierInput] | None = None
    status_history: list[EncounterStatusHistoryInput] | None = None
    class_history: list[EncounterClassHistoryInput] | None = None
    type: list[EncounterTypeInput] | None = None
    episode_of_care: list[EncounterEpisodeOfCareInput] | None = None
    based_on: list[EncounterBasedOnInput] | None = None
    appointment: list[EncounterAppointmentInput] | None = None
    reason_code: list[EncounterReasonCodeInput] | None = None
    reason_reference: list[EncounterReasonReferenceInput] | None = None
    account: list[EncounterAccountInput] | None = None
    participant: list[EncounterParticipantInput] | None = None
    diagnosis: list[EncounterDiagnosisInput] | None = None
    hospitalization: EncounterHospitalizationInput | None = None
    location: list[EncounterLocationInput] | None = None


class EncounterPatchSchema(BaseModel):
    """Partial update — only supplied fields are written. Every supplied
    sub-resource list (even `[]`) replaces the corresponding rows
    wholesale; omitted lists are left untouched. updated_by comes from
    the verified JWT, not a request body field."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"status": "finished", "period_end": "2026-02-01T10:00:00Z"}},
    )

    extension: list[dict] | None = None
    status: EncounterStatus | None = None
    class_coding: CodingInput | None = None
    service_type_coding: list[CodingInput] | None = None
    service_type_text: str | None = None
    priority_coding: list[CodingInput] | None = None
    priority_text: str | None = None

    subject: str | None = None
    subject_display: str | None = None
    subject_identifier_use: IdentifierUse | None = None
    subject_identifier_type_system: str | None = None
    subject_identifier_type_version: str | None = None
    subject_identifier_type_code: str | None = None
    subject_identifier_type_display: str | None = None
    subject_identifier_type_text: str | None = None
    subject_identifier_type_user_selected: bool | None = None
    subject_identifier_system: str | None = None
    subject_identifier_value: str | None = None
    subject_identifier_period_start: datetime | None = None
    subject_identifier_period_end: datetime | None = None

    period_start: datetime | None = None
    period_end: datetime | None = None

    length_value: Decimal | None = None
    length_comparator: EncounterLengthComparator | None = None
    length_unit: str | None = None
    length_system: str | None = None
    length_code: str | None = None

    service_provider: str | None = None
    service_provider_display: str | None = None
    service_provider_identifier_use: IdentifierUse | None = None
    service_provider_identifier_type_system: str | None = None
    service_provider_identifier_type_version: str | None = None
    service_provider_identifier_type_code: str | None = None
    service_provider_identifier_type_display: str | None = None
    service_provider_identifier_type_text: str | None = None
    service_provider_identifier_type_user_selected: bool | None = None
    service_provider_identifier_system: str | None = None
    service_provider_identifier_value: str | None = None
    service_provider_identifier_period_start: datetime | None = None
    service_provider_identifier_period_end: datetime | None = None

    part_of: str | None = None
    part_of_display: str | None = None
    part_of_identifier_use: IdentifierUse | None = None
    part_of_identifier_type_system: str | None = None
    part_of_identifier_type_version: str | None = None
    part_of_identifier_type_code: str | None = None
    part_of_identifier_type_display: str | None = None
    part_of_identifier_type_text: str | None = None
    part_of_identifier_type_user_selected: bool | None = None
    part_of_identifier_system: str | None = None
    part_of_identifier_value: str | None = None
    part_of_identifier_period_start: datetime | None = None
    part_of_identifier_period_end: datetime | None = None

    identifier: list[EncounterIdentifierInput] | None = None
    status_history: list[EncounterStatusHistoryInput] | None = None
    class_history: list[EncounterClassHistoryInput] | None = None
    type: list[EncounterTypeInput] | None = None
    episode_of_care: list[EncounterEpisodeOfCareInput] | None = None
    based_on: list[EncounterBasedOnInput] | None = None
    appointment: list[EncounterAppointmentInput] | None = None
    reason_code: list[EncounterReasonCodeInput] | None = None
    reason_reference: list[EncounterReasonReferenceInput] | None = None
    account: list[EncounterAccountInput] | None = None
    participant: list[EncounterParticipantInput] | None = None
    diagnosis: list[EncounterDiagnosisInput] | None = None
    hospitalization: EncounterHospitalizationInput | None = None
    location: list[EncounterLocationInput] | None = None
