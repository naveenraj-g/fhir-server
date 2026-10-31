from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)
from app.schemas.questionnaire.response import FHIRQuantity
from app.schemas.service_request.response.core import FHIRAnnotation

from .codeable_concept import PlainMedicationRequestCode, PlainMedicationRequestCodeableConcept
from .dosage_instruction import PlainMedicationRequestDosageInstruction
from .identifier import PlainMedicationRequestGroupIdentifier, PlainMedicationRequestIdentifier
from .note import PlainMedicationRequestNote
from .reference import (
    PlainMedicationRequestBasedOn,
    PlainMedicationRequestDetectedIssue,
    PlainMedicationRequestDispenseRequestPerformer,
    PlainMedicationRequestEncounter,
    PlainMedicationRequestEventHistory,
    PlainMedicationRequestInsurance,
    PlainMedicationRequestMedicationReference,
    PlainMedicationRequestPerformer,
    PlainMedicationRequestPriorPrescription,
    PlainMedicationRequestReasonReference,
    PlainMedicationRequestRecorder,
    PlainMedicationRequestReportedReference,
    PlainMedicationRequestRequester,
    PlainMedicationRequestSubject,
    PlainMedicationRequestSupportingInformation,
)

# ── FHIR (camelCase) ────────────────────────────────────────────────────────


class FHIRDosage(BaseModel):
    """FHIR R4 Dosage — https://www.hl7.org/fhir/R4/datatypes.html#Dosage
    `timing`/`doseAndRate`/`maxDosePerPeriod` are raw dicts — see
    app.models.medication_request.dosage_instruction's own docstring."""

    sequence: int | None = None
    text: str | None = None
    additionalInstruction: list[FHIRCodeableConcept] | None = None
    patientInstruction: str | None = None
    timing: dict | None = None
    asNeededBoolean: bool | None = None
    asNeededCodeableConcept: FHIRCodeableConcept | None = None
    site: FHIRCodeableConcept | None = None
    route: FHIRCodeableConcept | None = None
    method: FHIRCodeableConcept | None = None
    doseAndRate: list[dict] | None = None
    maxDosePerPeriod: dict | None = None
    maxDosePerAdministration: FHIRQuantity | None = None
    maxDosePerLifetime: FHIRQuantity | None = None


class FHIRMedicationRequestDispenseRequest(BaseModel):
    initialFillQuantity: FHIRQuantity | None = None
    initialFillDuration: FHIRQuantity | None = None
    dispenseInterval: FHIRQuantity | None = None
    validityPeriod: dict | None = None
    numberOfRepeatsAllowed: int | None = None
    quantity: FHIRQuantity | None = None
    expectedSupplyDuration: FHIRQuantity | None = None
    performer: FHIRReference | None = None


class FHIRMedicationRequestSubstitution(BaseModel):
    allowedBoolean: bool | None = None
    allowedCodeableConcept: FHIRCodeableConcept | None = None
    reason: FHIRCodeableConcept | None = None


class FHIRMedicationRequestSchema(BaseModel):
    resourceType: str = Field("MedicationRequest", description="Always 'MedicationRequest'.")
    id: str = Field(..., description="Public medication_request_id as a string.")
    meta: FHIRMeta | None = Field(None, description="Infrastructure-maintained resource metadata. Response-only.")
    extension: list[dict] | None = Field(None, description="Resource-level FHIR extensions.")
    identifier: list[FHIRIdentifier] | None = Field(None, description="Business identifiers.")
    status: str = Field(..., description="active | on-hold | cancelled | completed | entered-in-error | stopped | draft | unknown.")
    statusReason: FHIRCodeableConcept | None = Field(None, description="Reason for the current status.")
    intent: str = Field(..., description="proposal | plan | order | original-order | reflex-order | filler-order | instance-order | option.")
    category: list[FHIRCodeableConcept] | None = Field(None, description="Grouping/classification of the request.")
    priority: str | None = Field(None, description="routine | urgent | asap | stat.")
    doNotPerform: bool | None = Field(None, description="True if the medication should NOT be given.")
    reportedBoolean: bool | None = Field(None, description="reported[x]: boolean.")
    reportedReference: FHIRReference | None = Field(None, description="reported[x]: Reference.")
    medicationCodeableConcept: FHIRCodeableConcept | None = Field(None, description="medication[x]: CodeableConcept.")
    medicationReference: FHIRReference | None = Field(None, description="medication[x]: Reference(Medication).")
    subject: FHIRReference = Field(..., description="Individual/entity the medication is for.")
    encounter: FHIRReference | None = Field(None, description="Encounter this request was created during.")
    supportingInformation: list[FHIRReference] | None = Field(None, description="Additional clinical information.")
    authoredOn: str | None = Field(None, description="Date/time the request was initially authored.")
    requester: FHIRReference | None = Field(None, description="Who/what is requesting the medication.")
    performer: FHIRReference | None = Field(None, description="Intended performer of administration.")
    performerType: FHIRCodeableConcept | None = Field(None, description="Desired kind of performer.")
    recorder: FHIRReference | None = Field(None, description="Person who entered the request.")
    reasonCode: list[FHIRCodeableConcept] | None = Field(None, description="Reason/indication for the request, coded.")
    reasonReference: list[FHIRReference] | None = Field(None, description="Reason/indication for the request, resolved.")
    instantiatesCanonical: list[str] | None = Field(None, description="Canonical references instantiated.")
    instantiatesUri: list[str] | None = Field(None, description="External protocol/definition URIs instantiated.")
    basedOn: list[FHIRReference] | None = Field(None, description="Plan/proposal/order fulfilled by this request.")
    groupIdentifier: FHIRIdentifier | None = Field(None, description="Composite request this is part of.")
    courseOfTherapyType: FHIRCodeableConcept | None = Field(None, description="Overall pattern of medication administration.")
    insurance: list[FHIRReference] | None = Field(None, description="Associated insurance coverage.")
    note: list[FHIRAnnotation] | None = Field(None, description="Comments.")
    dosageInstruction: list[FHIRDosage] | None = Field(None, description="How the medication should be taken.")
    dispenseRequest: FHIRMedicationRequestDispenseRequest | None = Field(None, description="Medication supply authorization.")
    substitution: FHIRMedicationRequestSubstitution | None = Field(None, description="Whether substitution is allowed/not and why.")
    priorPrescription: FHIRReference | None = Field(None, description="The ultimate source of the prescription.")
    detectedIssue: list[FHIRReference] | None = Field(None, description="Clinical issues notified about.")
    eventHistory: list[FHIRReference] | None = Field(None, description="Key events in the history of the request.")


class FHIRMedicationRequestBundleEntry(BaseModel):
    resource: FHIRMedicationRequestSchema


class FHIRMedicationRequestBundle(FHIRBundle):
    entry: list[FHIRMedicationRequestBundleEntry] | None = None


# ── Plain (snake_case) ───────────────────────────────────────────────────────


class PlainMedicationRequestDispenseRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    initial_fill_quantity_value: float | None = None
    initial_fill_quantity_comparator: str | None = None
    initial_fill_quantity_unit: str | None = None
    initial_fill_quantity_system: str | None = None
    initial_fill_quantity_code: str | None = None
    initial_fill_duration_value: float | None = None
    initial_fill_duration_unit: str | None = None
    initial_fill_duration_system: str | None = None
    initial_fill_duration_code: str | None = None
    dispense_interval_value: float | None = None
    dispense_interval_unit: str | None = None
    dispense_interval_system: str | None = None
    dispense_interval_code: str | None = None
    validity_period_start: str | None = None
    validity_period_end: str | None = None
    number_of_repeats_allowed: int | None = None
    quantity_value: float | None = None
    quantity_unit: str | None = None
    quantity_system: str | None = None
    quantity_code: str | None = None
    expected_supply_duration_value: float | None = None
    expected_supply_duration_unit: str | None = None
    expected_supply_duration_system: str | None = None
    expected_supply_duration_code: str | None = None
    performer: PlainMedicationRequestDispenseRequestPerformer | None = None


class PlainMedicationRequestSubstitution(BaseModel):
    model_config = ConfigDict(extra="allow")
    allowed_boolean: bool | None = None
    allowed_codeable_concept: PlainMedicationRequestCode | None = None
    reason: PlainMedicationRequestCode | None = None


class PlainMedicationRequestResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public medication_request_id.")
    extension: list[dict] | None = Field(None, description="Resource-level FHIR extensions.")
    identifier: list[PlainMedicationRequestIdentifier] | None = Field(None, description="Business identifiers.")
    status: str | None = Field(None, description="active | on-hold | cancelled | completed | entered-in-error | stopped | draft | unknown.")
    status_reason: PlainMedicationRequestCode | None = Field(None, description="Reason for the current status.")
    intent: str | None = Field(None, description="proposal | plan | order | original-order | reflex-order | filler-order | instance-order | option.")
    category: list[PlainMedicationRequestCodeableConcept] | None = Field(None, description="Grouping/classification of the request.")
    priority: str | None = Field(None, description="routine | urgent | asap | stat.")
    do_not_perform: bool | None = Field(None, description="True if the medication should NOT be given.")
    reported_boolean: bool | None = Field(None, description="reported[x]: boolean.")
    reported_reference: PlainMedicationRequestReportedReference | None = Field(None, description="reported[x]: Reference.")
    medication_codeable_concept: PlainMedicationRequestCode | None = Field(None, description="medication[x]: CodeableConcept.")
    medication_reference: PlainMedicationRequestMedicationReference | None = Field(None, description="medication[x]: Reference(Medication).")
    subject: PlainMedicationRequestSubject | None = Field(None, description="Individual/entity the medication is for.")
    encounter: PlainMedicationRequestEncounter | None = Field(None, description="Encounter this request was created during.")
    supporting_information: list[PlainMedicationRequestSupportingInformation] | None = Field(None, description="Additional clinical information.")
    authored_on: str | None = Field(None, description="Date/time the request was initially authored.")
    requester: PlainMedicationRequestRequester | None = Field(None, description="Who/what is requesting the medication.")
    performer: PlainMedicationRequestPerformer | None = Field(None, description="Intended performer of administration.")
    performer_type: PlainMedicationRequestCode | None = Field(None, description="Desired kind of performer.")
    recorder: PlainMedicationRequestRecorder | None = Field(None, description="Person who entered the request.")
    reason_code: list[PlainMedicationRequestCodeableConcept] | None = Field(None, description="Reason/indication, coded.")
    reason_reference: list[PlainMedicationRequestReasonReference] | None = Field(None, description="Reason/indication, resolved.")
    instantiates_canonical: list[str] | None = Field(None, description="Canonical references instantiated.")
    instantiates_uri: list[str] | None = Field(None, description="External protocol/definition URIs instantiated.")
    based_on: list[PlainMedicationRequestBasedOn] | None = Field(None, description="Plan/proposal/order fulfilled by this request.")
    group_identifier: PlainMedicationRequestGroupIdentifier | None = Field(None, description="Composite request this is part of.")
    course_of_therapy_type: PlainMedicationRequestCode | None = Field(None, description="Overall pattern of medication administration.")
    insurance: list[PlainMedicationRequestInsurance] | None = Field(None, description="Associated insurance coverage.")
    note: list[PlainMedicationRequestNote] | None = Field(None, description="Comments.")
    dosage_instruction: list[PlainMedicationRequestDosageInstruction] | None = Field(None, description="How the medication should be taken.")
    dispense_request: PlainMedicationRequestDispenseRequest | None = Field(None, description="Medication supply authorization.")
    substitution: PlainMedicationRequestSubstitution | None = Field(None, description="Whether substitution is allowed/not and why.")
    prior_prescription: PlainMedicationRequestPriorPrescription | None = Field(None, description="The ultimate source of the prescription.")
    detected_issue: list[PlainMedicationRequestDetectedIssue] | None = Field(None, description="Clinical issues notified about.")
    event_history: list[PlainMedicationRequestEventHistory] | None = Field(None, description="Key events in the history of the request.")
    org_id: str | None = Field(None, description="Gateway-forwarded tenant/account ID — not a FHIR concept. Internally this column is named tenant_id.")
    created_at: str | None = Field(None, description="When this row was created.")
    updated_at: str | None = Field(None, description="When this row was last updated.")
    created_by: str | None = Field(None, description="Acting user who created this record.")
    updated_by: str | None = Field(None, description="Acting user who last updated this record.")


class PaginatedMedicationRequestResponse(BaseModel):
    total: int | None = Field(None, description="Total matching rows (null when total_mode=none).")
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Number of rows skipped before this page.")
    data: list[PlainMedicationRequestResponse]
