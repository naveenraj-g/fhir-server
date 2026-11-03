from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse, MedicationAdministrationStatus
from app.schemas.medication_administration.input.codeable_concept import (
    MedicationAdministrationCodeableConceptInput,
)
from app.schemas.medication_administration.input.dosage import (
    MedicationAdministrationDosageInput,
)
from app.schemas.medication_administration.input.identifier import (
    MedicationAdministrationIdentifierInput,
)
from app.schemas.medication_administration.input.note import (
    MedicationAdministrationNoteInput,
)
from app.schemas.medication_administration.input.performer import (
    MedicationAdministrationPerformerInput,
)
from app.schemas.medication_administration.input.reference import (
    MedicationAdministrationDeviceInput,
    MedicationAdministrationEventHistoryInput,
    MedicationAdministrationPartOfInput,
    MedicationAdministrationReasonReferenceInput,
    MedicationAdministrationSupportingInfoInput,
)

_CREATE_EXAMPLE: dict[str, Any] = {
    "status": "completed",
    "medication_codeable_concept": {
        "text": "Amoxicillin 500mg capsule",
        "coding": [
            {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "308182",
                "display": "Amoxicillin 500 MG Oral Capsule",
            }
        ],
    },
    "subject": "Patient/10001",
    "effective_date_time": "2026-11-03T10:00:00Z",
}


class MedicationAdministrationCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _CREATE_EXAMPLE},
    )

    status: MedicationAdministrationStatus = Field(
        ...,
        description="in-progress | not-done | on-hold | completed | entered-in-error | stopped | unknown.",
    )

    # category (0..1 CodeableConcept)
    category: MedicationAdministrationCodeableConceptInput | None = Field(
        None, description="Type of medication administration."
    )

    # medication[x] (1..1 choice: CodeableConcept | Reference(Medication))
    medication_codeable_concept: MedicationAdministrationCodeableConceptInput | None = Field(
        None, description="What was administered (CodeableConcept)."
    )
    medication_reference: str | None = Field(
        None, description="What was administered. Reference(Medication), e.g. 'Medication/250001'."
    )
    medication_display: str | None = Field(
        None, description="Display text for medication reference."
    )
    medication_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — purpose.")
    medication_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    medication_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    medication_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    medication_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    medication_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user selected.")
    medication_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    medication_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    medication_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    medication_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — period start.")
    medication_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — period end.")

    # subject (1..1 Reference(Patient | Group))
    subject: str = Field(
        ...,
        description="Who received administration. Reference(Patient | Group), e.g. 'Patient/10001'.",
    )
    subject_display: str | None = Field(None, description="Display text for subject.")
    subject_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — purpose.")
    subject_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    subject_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    subject_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    subject_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    subject_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user selected.")
    subject_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    subject_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    subject_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    subject_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — period start.")
    subject_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — period end.")

    # context (0..1 Reference(Encounter | EpisodeOfCare))
    context: str | None = Field(
        None,
        description="Encounter or Episode of Care administered as part of. Reference(Encounter | EpisodeOfCare), e.g. 'Encounter/20001'.",
    )
    context_display: str | None = Field(None, description="Display text for context.")
    context_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — purpose.")
    context_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    context_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    context_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    context_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    context_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user selected.")
    context_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    context_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    context_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    context_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — period start.")
    context_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — period end.")

    # effective[x] (1..1 choice: dateTime | Period)
    effective_date_time: datetime | None = Field(
        None, description="Start and end time of administration (dateTime)."
    )
    effective_period_start: datetime | None = Field(
        None, description="Start time of administration (Period.start)."
    )
    effective_period_end: datetime | None = Field(
        None, description="End time of administration (Period.end)."
    )

    # request (0..1 Reference(MedicationRequest))
    request: str | None = Field(
        None,
        description="Request that this administration is performed for. Reference(MedicationRequest), e.g. 'MedicationRequest/90001'.",
    )
    request_display: str | None = Field(None, description="Display text for request.")
    request_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — purpose.")
    request_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    request_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    request_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    request_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    request_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user selected.")
    request_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    request_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    request_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    request_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — period start.")
    request_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — period end.")

    # 0..* lists
    instantiates: list[str] | None = Field(
        None, description="Instantiates protocol or definition (0..* uri)."
    )
    part_of: list[MedicationAdministrationPartOfInput] | None = Field(
        None, description="Part of referenced event (0..* Reference(MedicationAdministration | Procedure))."
    )
    status_reason: list[MedicationAdministrationCodeableConceptInput] | None = Field(
        None, description="Reason administration not performed (0..* CodeableConcept)."
    )
    supporting_information: list[MedicationAdministrationSupportingInfoInput] | None = Field(
        None, description="Additional information supporting administration (0..* Reference(Any))."
    )
    performer: list[MedicationAdministrationPerformerInput] | None = Field(
        None, description="Who or what performed the medication administration (0..* BackboneElement)."
    )
    reason_code: list[MedicationAdministrationCodeableConceptInput] | None = Field(
        None, description="Reason administration performed (0..* CodeableConcept)."
    )
    reason_reference: list[MedicationAdministrationReasonReferenceInput] | None = Field(
        None, description="Condition or observation that supports why the medication was administered (0..* Reference)."
    )
    device: list[MedicationAdministrationDeviceInput] | None = Field(
        None, description="Device used to administer (0..* Reference(Device))."
    )
    note: list[MedicationAdministrationNoteInput] | None = Field(
        None, description="Information about the administration (0..* Annotation)."
    )
    dosage: MedicationAdministrationDosageInput | None = Field(
        None, description="Details of how medication was taken (0..1 BackboneElement)."
    )
    event_history: list[MedicationAdministrationEventHistoryInput] | None = Field(
        None, description="A list of relevant histories for the administration (0..* Reference(Provenance))."
    )
    identifier: list[MedicationAdministrationIdentifierInput] | None = Field(
        None, description="External identifier (0..* Identifier)."
    )
    extension: list[dict] | None = Field(
        None, description="Additional content defined by implementations."
    )


class MedicationAdministrationPatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: MedicationAdministrationStatus | None = Field(None, description="Status code.")
    category: MedicationAdministrationCodeableConceptInput | None = Field(None)
    medication_codeable_concept: MedicationAdministrationCodeableConceptInput | None = Field(None)
    medication_reference: str | None = Field(None)
    medication_display: str | None = Field(None)
    medication_identifier_use: IdentifierUse | None = Field(None)
    medication_identifier_type_system: str | None = Field(None)
    medication_identifier_type_version: str | None = Field(None)
    medication_identifier_type_code: str | None = Field(None)
    medication_identifier_type_display: str | None = Field(None)
    medication_identifier_type_user_selected: bool | None = Field(None)
    medication_identifier_type_text: str | None = Field(None)
    medication_identifier_system: str | None = Field(None)
    medication_identifier_value: str | None = Field(None)
    medication_identifier_period_start: datetime | None = Field(None)
    medication_identifier_period_end: datetime | None = Field(None)

    subject: str | None = Field(None)
    subject_display: str | None = Field(None)
    subject_identifier_use: IdentifierUse | None = Field(None)
    subject_identifier_type_system: str | None = Field(None)
    subject_identifier_type_version: str | None = Field(None)
    subject_identifier_type_code: str | None = Field(None)
    subject_identifier_type_display: str | None = Field(None)
    subject_identifier_type_user_selected: bool | None = Field(None)
    subject_identifier_type_text: str | None = Field(None)
    subject_identifier_system: str | None = Field(None)
    subject_identifier_value: str | None = Field(None)
    subject_identifier_period_start: datetime | None = Field(None)
    subject_identifier_period_end: datetime | None = Field(None)

    context: str | None = Field(None)
    context_display: str | None = Field(None)
    context_identifier_use: IdentifierUse | None = Field(None)
    context_identifier_type_system: str | None = Field(None)
    context_identifier_type_version: str | None = Field(None)
    context_identifier_type_code: str | None = Field(None)
    context_identifier_type_display: str | None = Field(None)
    context_identifier_type_user_selected: bool | None = Field(None)
    context_identifier_type_text: str | None = Field(None)
    context_identifier_system: str | None = Field(None)
    context_identifier_value: str | None = Field(None)
    context_identifier_period_start: datetime | None = Field(None)
    context_identifier_period_end: datetime | None = Field(None)

    effective_date_time: datetime | None = Field(None)
    effective_period_start: datetime | None = Field(None)
    effective_period_end: datetime | None = Field(None)

    request: str | None = Field(None)
    request_display: str | None = Field(None)
    request_identifier_use: IdentifierUse | None = Field(None)
    request_identifier_type_system: str | None = Field(None)
    request_identifier_type_version: str | None = Field(None)
    request_identifier_type_code: str | None = Field(None)
    request_identifier_type_display: str | None = Field(None)
    request_identifier_type_user_selected: bool | None = Field(None)
    request_identifier_type_text: str | None = Field(None)
    request_identifier_system: str | None = Field(None)
    request_identifier_value: str | None = Field(None)
    request_identifier_period_start: datetime | None = Field(None)
    request_identifier_period_end: datetime | None = Field(None)

    instantiates: list[str] | None = Field(None)
    part_of: list[MedicationAdministrationPartOfInput] | None = Field(None)
    status_reason: list[MedicationAdministrationCodeableConceptInput] | None = Field(None)
    supporting_information: list[MedicationAdministrationSupportingInfoInput] | None = Field(None)
    performer: list[MedicationAdministrationPerformerInput] | None = Field(None)
    reason_code: list[MedicationAdministrationCodeableConceptInput] | None = Field(None)
    reason_reference: list[MedicationAdministrationReasonReferenceInput] | None = Field(None)
    device: list[MedicationAdministrationDeviceInput] | None = Field(None)
    note: list[MedicationAdministrationNoteInput] | None = Field(None)
    dosage: MedicationAdministrationDosageInput | None = Field(None)
    event_history: list[MedicationAdministrationEventHistoryInput] | None = Field(None)
    identifier: list[MedicationAdministrationIdentifierInput] | None = Field(None)
    extension: list[dict] | None = Field(None)
