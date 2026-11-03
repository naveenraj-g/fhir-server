from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse, MedicationDispenseStatus
from app.schemas.medication_dispense.input.codeable_concept import (
    MedicationDispenseCodeableConceptInput,
)
from app.schemas.medication_dispense.input.dosage import (
    MedicationDispenseDosageInstructionInput,
)
from app.schemas.medication_dispense.input.identifier import (
    MedicationDispenseIdentifierInput,
)
from app.schemas.medication_dispense.input.note import (
    MedicationDispenseNoteInput,
)
from app.schemas.medication_dispense.input.performer import (
    MedicationDispensePerformerInput,
)
from app.schemas.medication_dispense.input.reference import (
    MedicationDispenseAuthorizingPrescriptionInput,
    MedicationDispenseDetectedIssueInput,
    MedicationDispenseEventHistoryInput,
    MedicationDispensePartOfInput,
    MedicationDispenseReceiverInput,
    MedicationDispenseSupportingInfoInput,
)
from app.schemas.medication_dispense.input.substitution import (
    MedicationDispenseSubstitutionInput,
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
    "when_prepared": "2026-11-03T09:00:00Z",
    "when_handed_over": "2026-11-03T10:00:00Z",
}


class MedicationDispenseCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _CREATE_EXAMPLE},
    )

    status: MedicationDispenseStatus = Field(
        ...,
        description="preparation | in-progress | cancelled | on-hold | completed | entered-in-error | stopped | declined | unknown.",
    )

    # statusReason[x] (0..1 choice: CodeableConcept | Reference(DetectedIssue))
    status_reason_codeable_concept: MedicationDispenseCodeableConceptInput | None = Field(
        None, description="Why a dispense was not performed."
    )
    status_reason_reference: str | None = Field(
        None, description="Why a dispense was not performed. Reference(DetectedIssue), e.g. 'DetectedIssue/540001'."
    )
    status_reason_reference_display: str | None = Field(
        None, description="Display text for status reason reference."
    )
    status_reason_reference_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — purpose.")
    status_reason_reference_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    status_reason_reference_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    status_reason_reference_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    status_reason_reference_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    status_reason_reference_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user selected.")
    status_reason_reference_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    status_reason_reference_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    status_reason_reference_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    status_reason_reference_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — period start.")
    status_reason_reference_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — period end.")

    # category (0..1 CodeableConcept)
    category: MedicationDispenseCodeableConceptInput | None = Field(
        None, description="Type of medication dispense."
    )

    # medication[x] (1..1 choice: CodeableConcept | Reference(Medication))
    medication_codeable_concept: MedicationDispenseCodeableConceptInput | None = Field(
        None, description="What medication was supplied (CodeableConcept)."
    )
    medication_reference: str | None = Field(
        None, description="What medication was supplied. Reference(Medication), e.g. 'Medication/250001'."
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

    # subject (0..1 Reference(Patient | Group))
    subject: str | None = Field(
        None,
        description="Who the dispense is for. Reference(Patient | Group), e.g. 'Patient/10001'.",
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
        description="Encounter / Episode associated with event. Reference(Encounter | EpisodeOfCare), e.g. 'Encounter/20001'.",
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

    # location (0..1 Reference(Location))
    location: str | None = Field(
        None,
        description="Where the dispense occurred. Reference(Location), e.g. 'Location/230001'.",
    )
    location_display: str | None = Field(None, description="Display text for location.")
    location_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — purpose.")
    location_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    location_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    location_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    location_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    location_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user selected.")
    location_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    location_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    location_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    location_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — period start.")
    location_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — period end.")

    # type (0..1 CodeableConcept)
    type: MedicationDispenseCodeableConceptInput | None = Field(
        None, description="Trial fill, partial fill, emergency fill, etc."
    )

    # quantity (0..1 SimpleQuantity)
    quantity_value: float | None = Field(None, description="Amount dispensed — value.")
    quantity_unit: str | None = Field(None, description="Amount dispensed — unit.")
    quantity_system: str | None = Field(None, description="Amount dispensed — unit system.")
    quantity_code: str | None = Field(None, description="Amount dispensed — unit code.")

    # daysSupply (0..1 SimpleQuantity)
    days_supply_value: float | None = Field(None, description="Amount of medication expressed as a timing amount — value.")
    days_supply_unit: str | None = Field(None, description="Amount of medication — unit.")
    days_supply_system: str | None = Field(None, description="Amount of medication — unit system.")
    days_supply_code: str | None = Field(None, description="Amount of medication — unit code.")

    # whenPrepared (0..1 dateTime)
    when_prepared: datetime | None = Field(None, description="When product was packaged and reviewed.")

    # whenHandedOver (0..1 dateTime)
    when_handed_over: datetime | None = Field(None, description="When product was given out.")

    # destination (0..1 Reference(Location))
    destination: str | None = Field(
        None,
        description="Where the medication was sent. Reference(Location), e.g. 'Location/230001'.",
    )
    destination_display: str | None = Field(None, description="Display text for destination.")
    destination_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — purpose.")
    destination_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    destination_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    destination_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    destination_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    destination_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user selected.")
    destination_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    destination_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    destination_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    destination_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — period start.")
    destination_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — period end.")

    # substitution (0..1 BackboneElement)
    substitution: MedicationDispenseSubstitutionInput | None = Field(
        None, description="Deals with substitution of one medicine for another."
    )

    # 0..* child lists
    identifier: list[MedicationDispenseIdentifierInput] | None = Field(None, description="External identifier.")
    part_of: list[MedicationDispensePartOfInput] | None = Field(None, description="Event that dispense is part of.")
    supporting_information: list[MedicationDispenseSupportingInfoInput] | None = Field(
        None, description="Information that supports the dispense."
    )
    performer: list[MedicationDispensePerformerInput] | None = Field(
        None, description="Who performed event."
    )
    authorizing_prescription: list[MedicationDispenseAuthorizingPrescriptionInput] | None = Field(
        None, description="Medication order that authorizes the dispense."
    )
    receiver: list[MedicationDispenseReceiverInput] | None = Field(
        None, description="Who collected the medication."
    )
    note: list[MedicationDispenseNoteInput] | None = Field(None, description="Information about the dispense.")
    dosage_instruction: list[MedicationDispenseDosageInstructionInput] | None = Field(
        None, description="How the medication is to be used by the patient."
    )
    detected_issue: list[MedicationDispenseDetectedIssueInput] | None = Field(
        None, description="Clinical issue with action."
    )
    event_history: list[MedicationDispenseEventHistoryInput] | None = Field(
        None, description="A list of relevant histories for the dispense."
    )

    extension: list[dict] | None = Field(None, description="Additional content defined by implementations.")


class MedicationDispensePatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: MedicationDispenseStatus | None = Field(
        None,
        description="preparation | in-progress | cancelled | on-hold | completed | entered-in-error | stopped | declined | unknown.",
    )

    # statusReason[x] (0..1 choice: CodeableConcept | Reference(DetectedIssue))
    status_reason_codeable_concept: MedicationDispenseCodeableConceptInput | None = Field(
        None, description="Why a dispense was not performed."
    )
    status_reason_reference: str | None = Field(
        None, description="Why a dispense was not performed. Reference(DetectedIssue), e.g. 'DetectedIssue/540001'."
    )
    status_reason_reference_display: str | None = Field(
        None, description="Display text for status reason reference."
    )
    status_reason_reference_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — purpose.")
    status_reason_reference_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    status_reason_reference_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    status_reason_reference_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    status_reason_reference_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    status_reason_reference_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user selected.")
    status_reason_reference_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    status_reason_reference_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    status_reason_reference_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    status_reason_reference_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — period start.")
    status_reason_reference_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — period end.")

    # category (0..1 CodeableConcept)
    category: MedicationDispenseCodeableConceptInput | None = Field(
        None, description="Type of medication dispense."
    )

    # medication[x] (1..1 choice: CodeableConcept | Reference(Medication))
    medication_codeable_concept: MedicationDispenseCodeableConceptInput | None = Field(
        None, description="What medication was supplied (CodeableConcept)."
    )
    medication_reference: str | None = Field(
        None, description="What medication was supplied. Reference(Medication), e.g. 'Medication/250001'."
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

    # subject (0..1 Reference(Patient | Group))
    subject: str | None = Field(
        None,
        description="Who the dispense is for. Reference(Patient | Group), e.g. 'Patient/10001'.",
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
        description="Encounter / Episode associated with event. Reference(Encounter | EpisodeOfCare), e.g. 'Encounter/20001'.",
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

    # location (0..1 Reference(Location))
    location: str | None = Field(
        None,
        description="Where the dispense occurred. Reference(Location), e.g. 'Location/230001'.",
    )
    location_display: str | None = Field(None, description="Display text for location.")
    location_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — purpose.")
    location_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    location_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    location_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    location_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    location_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user selected.")
    location_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    location_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    location_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    location_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — period start.")
    location_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — period end.")

    # type (0..1 CodeableConcept)
    type: MedicationDispenseCodeableConceptInput | None = Field(
        None, description="Trial fill, partial fill, emergency fill, etc."
    )

    # quantity (0..1 SimpleQuantity)
    quantity_value: float | None = Field(None, description="Amount dispensed — value.")
    quantity_unit: str | None = Field(None, description="Amount dispensed — unit.")
    quantity_system: str | None = Field(None, description="Amount dispensed — unit system.")
    quantity_code: str | None = Field(None, description="Amount dispensed — unit code.")

    # daysSupply (0..1 SimpleQuantity)
    days_supply_value: float | None = Field(None, description="Amount of medication expressed as a timing amount — value.")
    days_supply_unit: str | None = Field(None, description="Amount of medication — unit.")
    days_supply_system: str | None = Field(None, description="Amount of medication — unit system.")
    days_supply_code: str | None = Field(None, description="Amount of medication — unit code.")

    # whenPrepared (0..1 dateTime)
    when_prepared: datetime | None = Field(None, description="When product was packaged and reviewed.")

    # whenHandedOver (0..1 dateTime)
    when_handed_over: datetime | None = Field(None, description="When product was given out.")

    # destination (0..1 Reference(Location))
    destination: str | None = Field(
        None,
        description="Where the medication was sent. Reference(Location), e.g. 'Location/230001'.",
    )
    destination_display: str | None = Field(None, description="Display text for destination.")
    destination_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — purpose.")
    destination_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    destination_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    destination_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    destination_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    destination_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user selected.")
    destination_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    destination_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    destination_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    destination_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — period start.")
    destination_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — period end.")

    # substitution (0..1 BackboneElement)
    substitution: MedicationDispenseSubstitutionInput | None = Field(
        None, description="Deals with substitution of one medicine for another."
    )

    # 0..* child lists
    identifier: list[MedicationDispenseIdentifierInput] | None = Field(None, description="External identifier.")
    part_of: list[MedicationDispensePartOfInput] | None = Field(None, description="Event that dispense is part of.")
    supporting_information: list[MedicationDispenseSupportingInfoInput] | None = Field(
        None, description="Information that supports the dispense."
    )
    performer: list[MedicationDispensePerformerInput] | None = Field(
        None, description="Who performed event."
    )
    authorizing_prescription: list[MedicationDispenseAuthorizingPrescriptionInput] | None = Field(
        None, description="Medication order that authorizes the dispense."
    )
    receiver: list[MedicationDispenseReceiverInput] | None = Field(
        None, description="Who collected the medication."
    )
    note: list[MedicationDispenseNoteInput] | None = Field(None, description="Information about the dispense.")
    dosage_instruction: list[MedicationDispenseDosageInstructionInput] | None = Field(
        None, description="How the medication is to be used by the patient."
    )
    detected_issue: list[MedicationDispenseDetectedIssueInput] | None = Field(
        None, description="Clinical issue with action."
    )
    event_history: list[MedicationDispenseEventHistoryInput] | None = Field(
        None, description="A list of relevant histories for the dispense."
    )

    extension: list[dict] | None = Field(None, description="Additional content defined by implementations.")
