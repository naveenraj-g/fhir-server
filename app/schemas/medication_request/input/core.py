from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import (
    MedicationRequestIntent,
    MedicationRequestPriority,
    MedicationRequestQuantityComparator,
    MedicationRequestStatus,
)

from .codeable_concept import MedicationRequestCodeableConceptInput
from .dosage_instruction import MedicationRequestDosageInstructionInput
from .identifier import MedicationRequestIdentifierInput
from .note import MedicationRequestNoteInput
from .reference import (
    MedicationRequestBasedOnInput,
    MedicationRequestDetectedIssueInput,
    MedicationRequestDispenseRequestPerformerInput,
    MedicationRequestEncounterInput,
    MedicationRequestEventHistoryInput,
    MedicationRequestInsuranceInput,
    MedicationRequestMedicationReferenceInput,
    MedicationRequestPerformerInput,
    MedicationRequestPriorPrescriptionInput,
    MedicationRequestReasonReferenceInput,
    MedicationRequestRecorderInput,
    MedicationRequestReportedReferenceInput,
    MedicationRequestRequesterInput,
    MedicationRequestSubjectInput,
    MedicationRequestSupportingInformationInput,
)

_EXAMPLE = {
    "user_id": "user-001",
    "tenant_id": "org-001",
    "created_by": "user-001",
    "status": "active",
    "intent": "order",
    "subject": {"reference": "Patient/10001"},
    "medication_codeable_concept": {"text": "Amoxicillin 500mg capsule"},
    "authored_on": "2026-01-15T10:30:00Z",
}


class MedicationRequestCreateSchema(BaseModel):
    """Creates a MedicationRequest and any combination of its sub-resource
    lists atomically in one request. Default (gateway-trusted) pattern —
    NOT part of the JWT auth rollout, same as QuestionnaireResponse/
    ServiceRequest: `tenant_id`/`created_by` are plain, gateway-forwarded
    request fields."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": _EXAMPLE})

    user_id: str | None = Field(None, description="Gateway-forwarded ID of the end-user this record is scoped to.")
    tenant_id: str = Field(..., description="Gateway-forwarded ID of the tenant/account this record is scoped to.")
    created_by: str = Field(..., description="Gateway-forwarded ID of the acting user who created this record.")

    extension: list[dict] | None = Field(None, description="Resource-level FHIR extensions.")

    identifier: list[MedicationRequestIdentifierInput] | None = Field(None, description="Business identifiers.")
    status: MedicationRequestStatus = Field(..., description="active | on-hold | cancelled | completed | entered-in-error | stopped | draft | unknown.")
    status_reason: MedicationRequestCodeableConceptInput | None = Field(None, description="Reason for the current status.")
    intent: MedicationRequestIntent = Field(..., description="proposal | plan | order | original-order | reflex-order | filler-order | instance-order | option.")
    category: list[MedicationRequestCodeableConceptInput] | None = Field(None, description="Grouping/classification of the request.")
    priority: MedicationRequestPriority | None = Field(None, description="routine | urgent | asap | stat.")
    do_not_perform: bool | None = Field(None, description="True if the medication should NOT be given.")

    # reported[x]
    reported_boolean: bool | None = Field(None, description="reported[x]: boolean.")
    reported_reference: MedicationRequestReportedReferenceInput | None = Field(None, description="reported[x]: Reference.")

    # medication[x] (1..1 required)
    medication_codeable_concept: MedicationRequestCodeableConceptInput | None = Field(None, description="medication[x]: CodeableConcept.")
    medication_reference: MedicationRequestMedicationReferenceInput | None = Field(None, description="medication[x]: Reference(Medication).")

    subject: MedicationRequestSubjectInput = Field(..., description="Individual/entity the medication is for (1..1, required).")
    encounter: MedicationRequestEncounterInput | None = Field(None, description="Encounter this request was created during.")
    supporting_information: list[MedicationRequestSupportingInformationInput] | None = Field(None, description="Additional clinical information.")
    authored_on: datetime | None = Field(None, description="Date/time the request was initially authored.")
    requester: MedicationRequestRequesterInput | None = Field(None, description="Who/what is requesting the medication.")
    performer: MedicationRequestPerformerInput | None = Field(None, description="Intended performer of administration.")
    performer_type: MedicationRequestCodeableConceptInput | None = Field(None, description="Desired kind of performer.")
    recorder: MedicationRequestRecorderInput | None = Field(None, description="Person who entered the request.")
    reason_code: list[MedicationRequestCodeableConceptInput] | None = Field(None, description="Reason/indication for the request, coded.")
    reason_reference: list[MedicationRequestReasonReferenceInput] | None = Field(None, description="Reason/indication for the request, resolved.")
    instantiates_canonical: list[str] | None = Field(None, description="Canonical references instantiated.")
    instantiates_uri: list[str] | None = Field(None, description="External protocol/definition URIs instantiated.")
    based_on: list[MedicationRequestBasedOnInput] | None = Field(None, description="Plan/proposal/order fulfilled by this request.")
    group_identifier: MedicationRequestIdentifierInput | None = Field(None, description="Composite request this is part of.")
    course_of_therapy_type: MedicationRequestCodeableConceptInput | None = Field(None, description="Overall pattern of medication administration.")
    insurance: list[MedicationRequestInsuranceInput] | None = Field(None, description="Associated insurance coverage.")
    note: list[MedicationRequestNoteInput] | None = Field(None, description="Comments.")
    dosage_instruction: list[MedicationRequestDosageInstructionInput] | None = Field(None, description="How the medication should be taken.")

    # dispenseRequest (0..1, flattened)
    dispense_request_initial_fill_quantity_value: float | None = Field(None, description="dispenseRequest.initialFill.quantity — numeric value.")
    dispense_request_initial_fill_quantity_comparator: MedicationRequestQuantityComparator | None = Field(None, description="dispenseRequest.initialFill.quantity — comparator.")
    dispense_request_initial_fill_quantity_unit: str | None = Field(None, description="dispenseRequest.initialFill.quantity — unit.")
    dispense_request_initial_fill_quantity_system: str | None = Field(None, description="dispenseRequest.initialFill.quantity — unit system.")
    dispense_request_initial_fill_quantity_code: str | None = Field(None, description="dispenseRequest.initialFill.quantity — coded unit form.")
    dispense_request_initial_fill_duration_value: float | None = Field(None, description="dispenseRequest.initialFill.duration — numeric value.")
    dispense_request_initial_fill_duration_unit: str | None = Field(None, description="dispenseRequest.initialFill.duration — unit.")
    dispense_request_initial_fill_duration_system: str | None = Field(None, description="dispenseRequest.initialFill.duration — unit system.")
    dispense_request_initial_fill_duration_code: str | None = Field(None, description="dispenseRequest.initialFill.duration — coded unit form.")
    dispense_request_dispense_interval_value: float | None = Field(None, description="dispenseRequest.dispenseInterval — numeric value.")
    dispense_request_dispense_interval_unit: str | None = Field(None, description="dispenseRequest.dispenseInterval — unit.")
    dispense_request_dispense_interval_system: str | None = Field(None, description="dispenseRequest.dispenseInterval — unit system.")
    dispense_request_dispense_interval_code: str | None = Field(None, description="dispenseRequest.dispenseInterval — coded unit form.")
    dispense_request_validity_period_start: datetime | None = Field(None, description="dispenseRequest.validityPeriod — start.")
    dispense_request_validity_period_end: datetime | None = Field(None, description="dispenseRequest.validityPeriod — end.")
    dispense_request_number_of_repeats_allowed: int | None = Field(None, description="dispenseRequest.numberOfRepeatsAllowed.")
    dispense_request_quantity_value: float | None = Field(None, description="dispenseRequest.quantity — numeric value.")
    dispense_request_quantity_unit: str | None = Field(None, description="dispenseRequest.quantity — unit.")
    dispense_request_quantity_system: str | None = Field(None, description="dispenseRequest.quantity — unit system.")
    dispense_request_quantity_code: str | None = Field(None, description="dispenseRequest.quantity — coded unit form.")
    dispense_request_expected_supply_duration_value: float | None = Field(None, description="dispenseRequest.expectedSupplyDuration — numeric value.")
    dispense_request_expected_supply_duration_unit: str | None = Field(None, description="dispenseRequest.expectedSupplyDuration — unit.")
    dispense_request_expected_supply_duration_system: str | None = Field(None, description="dispenseRequest.expectedSupplyDuration — unit system.")
    dispense_request_expected_supply_duration_code: str | None = Field(None, description="dispenseRequest.expectedSupplyDuration — coded unit form.")
    dispense_request_performer: MedicationRequestDispenseRequestPerformerInput | None = Field(None, description="dispenseRequest.performer — Reference(Organization).")

    # substitution (0..1, flattened)
    substitution_allowed_boolean: bool | None = Field(None, description="substitution.allowed[x]: boolean.")
    substitution_allowed_codeable_concept: MedicationRequestCodeableConceptInput | None = Field(None, description="substitution.allowed[x]: CodeableConcept.")
    substitution_reason: MedicationRequestCodeableConceptInput | None = Field(None, description="substitution.reason.")

    prior_prescription: MedicationRequestPriorPrescriptionInput | None = Field(None, description="The ultimate source of the prescription.")
    detected_issue: list[MedicationRequestDetectedIssueInput] | None = Field(None, description="Clinical issues notified about.")
    event_history: list[MedicationRequestEventHistoryInput] | None = Field(None, description="Key events in the history of the request.")


class MedicationRequestPatchSchema(BaseModel):
    """Partial update — only supplied fields are written. Every supplied
    sub-resource list (even `[]`) replaces the corresponding rows
    wholesale; omitted lists are left untouched."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"updated_by": "user-001", "status": "completed"}})

    updated_by: str | None = Field(None, description="Gateway-forwarded ID of the acting user making this update.")

    extension: list[dict] | None = Field(None, description="Replaces the full list if supplied.")
    identifier: list[MedicationRequestIdentifierInput] | None = Field(None, description="Replaces the full list if supplied.")
    status: MedicationRequestStatus | None = Field(None, description="active | on-hold | cancelled | completed | entered-in-error | stopped | draft | unknown.")
    status_reason: MedicationRequestCodeableConceptInput | None = Field(None, description="Set to null to clear.")
    intent: MedicationRequestIntent | None = Field(None, description="proposal | plan | order | original-order | reflex-order | filler-order | instance-order | option.")
    category: list[MedicationRequestCodeableConceptInput] | None = Field(None, description="Replaces the full list if supplied.")
    priority: MedicationRequestPriority | None = Field(None, description="routine | urgent | asap | stat.")
    do_not_perform: bool | None = Field(None, description="True if the medication should NOT be given.")

    reported_boolean: bool | None = Field(None, description="reported[x]: boolean.")
    reported_reference: MedicationRequestReportedReferenceInput | None = Field(None, description="reported[x]: Reference.")

    medication_codeable_concept: MedicationRequestCodeableConceptInput | None = Field(None, description="medication[x]: CodeableConcept.")
    medication_reference: MedicationRequestMedicationReferenceInput | None = Field(None, description="medication[x]: Reference(Medication).")

    subject: MedicationRequestSubjectInput | None = Field(None, description="Set to null to clear (not recommended — subject is 1..1 in FHIR).")
    encounter: MedicationRequestEncounterInput | None = Field(None, description="Set to null to clear.")
    supporting_information: list[MedicationRequestSupportingInformationInput] | None = Field(None, description="Replaces the full list if supplied.")
    authored_on: datetime | None = Field(None, description="Date/time the request was initially authored.")
    requester: MedicationRequestRequesterInput | None = Field(None, description="Set to null to clear.")
    performer: MedicationRequestPerformerInput | None = Field(None, description="Set to null to clear.")
    performer_type: MedicationRequestCodeableConceptInput | None = Field(None, description="Set to null to clear.")
    recorder: MedicationRequestRecorderInput | None = Field(None, description="Set to null to clear.")
    reason_code: list[MedicationRequestCodeableConceptInput] | None = Field(None, description="Replaces the full list if supplied.")
    reason_reference: list[MedicationRequestReasonReferenceInput] | None = Field(None, description="Replaces the full list if supplied.")
    instantiates_canonical: list[str] | None = Field(None, description="Replaces the full list if supplied.")
    instantiates_uri: list[str] | None = Field(None, description="Replaces the full list if supplied.")
    based_on: list[MedicationRequestBasedOnInput] | None = Field(None, description="Replaces the full list if supplied.")
    group_identifier: MedicationRequestIdentifierInput | None = Field(None, description="Set to null to clear.")
    course_of_therapy_type: MedicationRequestCodeableConceptInput | None = Field(None, description="Set to null to clear.")
    insurance: list[MedicationRequestInsuranceInput] | None = Field(None, description="Replaces the full list if supplied.")
    note: list[MedicationRequestNoteInput] | None = Field(None, description="Replaces the full list if supplied.")
    dosage_instruction: list[MedicationRequestDosageInstructionInput] | None = Field(None, description="Replaces the full list if supplied.")

    dispense_request_initial_fill_quantity_value: float | None = Field(None, description="dispenseRequest.initialFill.quantity — numeric value.")
    dispense_request_initial_fill_quantity_comparator: MedicationRequestQuantityComparator | None = Field(None, description="dispenseRequest.initialFill.quantity — comparator.")
    dispense_request_initial_fill_quantity_unit: str | None = Field(None, description="dispenseRequest.initialFill.quantity — unit.")
    dispense_request_initial_fill_quantity_system: str | None = Field(None, description="dispenseRequest.initialFill.quantity — unit system.")
    dispense_request_initial_fill_quantity_code: str | None = Field(None, description="dispenseRequest.initialFill.quantity — coded unit form.")
    dispense_request_initial_fill_duration_value: float | None = Field(None, description="dispenseRequest.initialFill.duration — numeric value.")
    dispense_request_initial_fill_duration_unit: str | None = Field(None, description="dispenseRequest.initialFill.duration — unit.")
    dispense_request_initial_fill_duration_system: str | None = Field(None, description="dispenseRequest.initialFill.duration — unit system.")
    dispense_request_initial_fill_duration_code: str | None = Field(None, description="dispenseRequest.initialFill.duration — coded unit form.")
    dispense_request_dispense_interval_value: float | None = Field(None, description="dispenseRequest.dispenseInterval — numeric value.")
    dispense_request_dispense_interval_unit: str | None = Field(None, description="dispenseRequest.dispenseInterval — unit.")
    dispense_request_dispense_interval_system: str | None = Field(None, description="dispenseRequest.dispenseInterval — unit system.")
    dispense_request_dispense_interval_code: str | None = Field(None, description="dispenseRequest.dispenseInterval — coded unit form.")
    dispense_request_validity_period_start: datetime | None = Field(None, description="dispenseRequest.validityPeriod — start.")
    dispense_request_validity_period_end: datetime | None = Field(None, description="dispenseRequest.validityPeriod — end.")
    dispense_request_number_of_repeats_allowed: int | None = Field(None, description="dispenseRequest.numberOfRepeatsAllowed.")
    dispense_request_quantity_value: float | None = Field(None, description="dispenseRequest.quantity — numeric value.")
    dispense_request_quantity_unit: str | None = Field(None, description="dispenseRequest.quantity — unit.")
    dispense_request_quantity_system: str | None = Field(None, description="dispenseRequest.quantity — unit system.")
    dispense_request_quantity_code: str | None = Field(None, description="dispenseRequest.quantity — coded unit form.")
    dispense_request_expected_supply_duration_value: float | None = Field(None, description="dispenseRequest.expectedSupplyDuration — numeric value.")
    dispense_request_expected_supply_duration_unit: str | None = Field(None, description="dispenseRequest.expectedSupplyDuration — unit.")
    dispense_request_expected_supply_duration_system: str | None = Field(None, description="dispenseRequest.expectedSupplyDuration — unit system.")
    dispense_request_expected_supply_duration_code: str | None = Field(None, description="dispenseRequest.expectedSupplyDuration — coded unit form.")
    dispense_request_performer: MedicationRequestDispenseRequestPerformerInput | None = Field(None, description="Set to null to clear.")

    substitution_allowed_boolean: bool | None = Field(None, description="substitution.allowed[x]: boolean.")
    substitution_allowed_codeable_concept: MedicationRequestCodeableConceptInput | None = Field(None, description="substitution.allowed[x]: CodeableConcept.")
    substitution_reason: MedicationRequestCodeableConceptInput | None = Field(None, description="substitution.reason.")

    prior_prescription: MedicationRequestPriorPrescriptionInput | None = Field(None, description="Set to null to clear.")
    detected_issue: list[MedicationRequestDetectedIssueInput] | None = Field(None, description="Replaces the full list if supplied.")
    event_history: list[MedicationRequestEventHistoryInput] | None = Field(None, description="Replaces the full list if supplied.")
