from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ── Shared CodeableConcept input ───────────────────────────────────────────────


class _CodeableConceptInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


# ── Sub-resource input schemas ─────────────────────────────────────────────────


class EncounterIdentifierInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: Optional[str] = Field(None, description="usual|official|temp|secondary|old")
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    system: Optional[str] = None
    value: str = Field(..., description="Identifier value.")
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    assigner: Optional[str] = None


class EncounterStatusHistoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str = Field(..., description="planned|arrived|triaged|in-progress|onleave|finished|cancelled|entered-in-error|unknown")
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class EncounterClassHistoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    class_system: Optional[str] = None
    class_version: Optional[str] = None
    class_code: str = Field(..., description="Class code, e.g. 'AMB', 'IMP', 'EMER'.")
    class_display: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class EncounterTypeInput(_CodeableConceptInput):
    """type[] (0..*) CodeableConcept."""


class EncounterEpisodeOfCareInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="FHIR reference, e.g. 'EpisodeOfCare/501'.")
    reference_display: Optional[str] = None


class EncounterBasedOnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="FHIR reference, e.g. 'ServiceRequest/80001'.")
    reference_display: Optional[str] = None


class EncounterParticipantTypeInput(_CodeableConceptInput):
    """participant.type[] (0..*) CodeableConcept."""


class EncounterParticipantInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Optional[List[EncounterParticipantTypeInput]] = None
    reference: Optional[str] = Field(
        None,
        description="FHIR individual reference, e.g. 'Practitioner/30001'. Allowed: Practitioner|PractitionerRole|RelatedPerson.",
    )
    reference_display: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class EncounterAppointmentRefInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="FHIR reference, e.g. 'Appointment/40001'.")
    reference_display: Optional[str] = None


class EncounterReasonCodeInput(_CodeableConceptInput):
    """reasonCode[] (0..*) CodeableConcept."""


class EncounterReasonReferenceInput(BaseModel):
    """reasonReference[] (0..*) Reference(Condition|Procedure|Observation|ImmunizationRecommendation)."""
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="FHIR reference, e.g. 'Condition/120001'.")
    reference_display: Optional[str] = None


class EncounterDiagnosisInput(BaseModel):
    """diagnosis[] (0..*) BackboneElement — condition (1..1), use (0..1 CodeableConcept), rank (0..1)."""
    model_config = ConfigDict(extra="forbid")
    condition: str = Field(..., description="FHIR reference, e.g. 'Condition/120001' or 'Procedure/100001'.")
    condition_display: Optional[str] = None
    use_system: Optional[str] = None
    use_code: Optional[str] = None
    use_display: Optional[str] = None
    use_text: Optional[str] = None
    rank: Optional[int] = Field(None, description="Ranking of the diagnosis (1 = highest priority).")


class EncounterAccountInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="FHIR reference, e.g. 'Account/501'.")
    reference_display: Optional[str] = None


class EncounterHospitalizationInput(BaseModel):
    """hospitalization (0..1 BackboneElement)."""
    model_config = ConfigDict(extra="forbid")
    pre_admission_identifier_system: Optional[str] = None
    pre_admission_identifier_value: Optional[str] = None
    origin: Optional[str] = Field(None, description="Reference to origin Location or Organization, e.g. 'Location/123'.")
    origin_display: Optional[str] = None
    admit_source_system: Optional[str] = None
    admit_source_code: Optional[str] = None
    admit_source_display: Optional[str] = None
    admit_source_text: Optional[str] = None
    re_admission_system: Optional[str] = None
    re_admission_code: Optional[str] = None
    re_admission_display: Optional[str] = None
    re_admission_text: Optional[str] = None
    diet_preference: Optional[List[_CodeableConceptInput]] = None
    special_courtesy: Optional[List[_CodeableConceptInput]] = None
    special_arrangement: Optional[List[_CodeableConceptInput]] = None
    destination: Optional[str] = Field(None, description="Reference to destination Location or Organization, e.g. 'Location/456'.")
    destination_display: Optional[str] = None
    discharge_disposition_system: Optional[str] = None
    discharge_disposition_code: Optional[str] = None
    discharge_disposition_display: Optional[str] = None
    discharge_disposition_text: Optional[str] = None


class EncounterLocationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="FHIR reference to the Location, e.g. 'Location/501'.")
    reference_display: Optional[str] = None
    status: Optional[str] = Field(None, description="planned|active|reserved|completed")
    physical_type_system: Optional[str] = None
    physical_type_code: Optional[str] = None
    physical_type_display: Optional[str] = None
    physical_type_text: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


# ── Encounter create / patch ───────────────────────────────────────────────────


class EncounterCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "user_id": "user-uuid-123",
                "org_id": "org-uuid-456",
                "status": "in-progress",
                "class_system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "class_code": "AMB",
                "class_display": "ambulatory",
                "priority_code": "17621005",
                "priority_system": "http://snomed.info/sct",
                "priority_display": "Normal",
                "subject": "Patient/10001",
                "period_start": "2026-04-01T09:00:00Z",
                "service_type_code": "11429006",
                "service_type_system": "http://snomed.info/sct",
                "service_type_display": "Consultation",
                "type": [
                    {
                        "coding_system": "http://snomed.info/sct",
                        "coding_code": "185349003",
                        "coding_display": "Encounter for check up",
                        "text": "Check up",
                    }
                ],
                "participant": [
                    {
                        "type": [{"coding_code": "PART", "text": "Participant"}],
                        "reference": "Practitioner/30001",
                        "period_start": "2026-04-01T09:00:00Z",
                    }
                ],
            }
        },
    )

    user_id: Optional[str] = None
    org_id: Optional[str] = None
    created_by: Optional[str] = None

    # status (1..1)
    status: str = Field(..., description="planned|arrived|triaged|in-progress|onleave|finished|cancelled|entered-in-error|unknown")

    # class (1..1 Coding) — flattened
    class_system: Optional[str] = None
    class_code: str = Field(..., description="Class code, e.g. 'AMB', 'IMP', 'EMER' (required).")
    class_display: Optional[str] = None

    # serviceType (0..1 CodeableConcept) — flattened
    service_type_system: Optional[str] = None
    service_type_code: Optional[str] = None
    service_type_display: Optional[str] = None
    service_type_text: Optional[str] = None

    # priority (0..1 CodeableConcept)
    priority_system: Optional[str] = None
    priority_code: Optional[str] = None
    priority_display: Optional[str] = None
    priority_text: Optional[str] = None

    # subject (0..1 Reference(Patient|Group))
    subject: Optional[str] = Field(None, description="Patient or Group reference, e.g. 'Patient/10001'.")

    # period (0..1 Period)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    # length (0..1 Duration)
    length_value: Optional[float] = None
    length_comparator: Optional[str] = Field(None, description="<|<=|>=|>")
    length_unit: Optional[str] = None
    length_system: Optional[str] = None
    length_code: Optional[str] = None

    # serviceProvider (0..1 Reference(Organization))
    service_provider: Optional[str] = Field(None, description="FHIR reference, e.g. 'Organization/190001'.")
    service_provider_display: Optional[str] = None

    # partOf (0..1 Reference(Encounter))
    part_of: Optional[str] = Field(None, description="FHIR reference, e.g. 'Encounter/20001'.")

    # Sub-resource arrays
    identifier: Optional[List[EncounterIdentifierInput]] = None
    status_history: Optional[List[EncounterStatusHistoryInput]] = None
    class_history: Optional[List[EncounterClassHistoryInput]] = None
    type: Optional[List[EncounterTypeInput]] = None
    episode_of_care: Optional[List[EncounterEpisodeOfCareInput]] = None
    based_on: Optional[List[EncounterBasedOnInput]] = None
    participant: Optional[List[EncounterParticipantInput]] = None
    appointment: Optional[List[EncounterAppointmentRefInput]] = None
    reason_code: Optional[List[EncounterReasonCodeInput]] = None
    reason_reference: Optional[List[EncounterReasonReferenceInput]] = None
    diagnosis: Optional[List[EncounterDiagnosisInput]] = None
    account: Optional[List[EncounterAccountInput]] = None
    hospitalization: Optional[EncounterHospitalizationInput] = None
    location: Optional[List[EncounterLocationInput]] = None


class EncounterPatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Optional[str] = Field(None, description="planned|arrived|triaged|in-progress|onleave|finished|cancelled|entered-in-error|unknown")
    period_end: Optional[datetime] = Field(None, description="Close the encounter by setting the period end time.")
    priority_system: Optional[str] = None
    priority_code: Optional[str] = None
    priority_display: Optional[str] = None
    priority_text: Optional[str] = None
    service_type_system: Optional[str] = None
    service_type_code: Optional[str] = None
    service_type_display: Optional[str] = None
    service_type_text: Optional[str] = None
    updated_by: Optional[str] = None
