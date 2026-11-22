from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRQuantity,
    FHIRReference,
)
from app.schemas.datatypes.annotation import FHIRAnnotation
from app.schemas.datatypes.dosage import FHIRDosage
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRMedicationRequestInitialFill(BaseModel):
    quantity: FHIRQuantity | None = Field(None, description="First fill quantity.")
    duration: FHIRQuantity | None = Field(None, description="First fill duration.")


class FHIRMedicationRequestDispenseRequest(BaseModel):
    initialFill: FHIRMedicationRequestInitialFill | None = Field(
        None, description="First fill details."
    )
    dispenseInterval: FHIRQuantity | None = Field(
        None, description="Minimum period of time between dispenses."
    )
    validityPeriod: FHIRPeriod | None = Field(
        None, description="Time period supply is authorized for."
    )
    numberOfRepeatsAllowed: int | None = Field(
        None, description="Number of refills authorized."
    )
    quantity: FHIRQuantity | None = Field(
        None, description="Amount of medication to supply per dispense."
    )
    expectedSupplyDuration: FHIRQuantity | None = Field(
        None, description="Number of days supply per dispense."
    )
    performer: FHIRReference | None = Field(None, description="Intended dispenser.")


class FHIRMedicationRequestSubstitution(BaseModel):
    allowedBoolean: bool | None = Field(
        None, description="Whether substitution is allowed or not."
    )
    allowedCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="What type of substitution is allowed."
    )
    reason: FHIRCodeableConcept | None = Field(
        None, description="Why should (not) substitution be made."
    )


class FHIRMedicationRequestSchema(BaseModel):
    resourceType: str = Field(
        "MedicationRequest", description="Always 'MedicationRequest'."
    )
    id: str = Field(..., description="Public medication_request_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External ids for this request."
    )
    status: str | None = Field(
        None,
        description="active | on-hold | cancelled | completed | entered-in-error | stopped | draft | unknown.",
    )
    statusReason: FHIRCodeableConcept | None = Field(
        None, description="Reason for current status."
    )
    intent: str | None = Field(
        None,
        description="proposal | plan | order | original-order | reflex-order | filler-order | instance-order | option.",
    )
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="Type of medication usage."
    )
    priority: str | None = Field(None, description="routine | urgent | asap | stat.")
    doNotPerform: bool | None = Field(
        None, description="True if request is prohibiting action."
    )
    reportedBoolean: bool | None = Field(
        None, description="Reported rather than primary record (boolean)."
    )
    reportedReference: FHIRReference | None = Field(
        None, description="Reported rather than primary record (Reference)."
    )
    medicationCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="Medication to be taken (CodeableConcept)."
    )
    medicationReference: FHIRReference | None = Field(
        None, description="Medication to be taken (Reference(Medication))."
    )
    subject: FHIRReference | None = Field(
        None, description="Who or group medication request is for."
    )
    encounter: FHIRReference | None = Field(
        None, description="Encounter created as part of encounter/admission/stay."
    )
    supportingInformation: list[FHIRReference] | None = Field(
        None, description="Information to support ordering of the medication."
    )
    authoredOn: str | None = Field(
        None, description="When request was initially authored."
    )
    requester: FHIRReference | None = Field(
        None, description="Who/What requested the Request."
    )
    performer: FHIRReference | None = Field(
        None, description="Intended performer of administration."
    )
    performerType: FHIRCodeableConcept | None = Field(
        None, description="Desired kind of performer of the medication administration."
    )
    recorder: FHIRReference | None = Field(
        None, description="Person who entered the request."
    )
    reasonCode: list[FHIRCodeableConcept] | None = Field(
        None,
        description="Reason or indication for ordering or not ordering the medication.",
    )
    reasonReference: list[FHIRReference] | None = Field(
        None,
        description="Condition or observation that supports why the prescription is being written.",
    )
    instantiatesCanonical: list[str] | None = Field(
        None, description="Instantiates FHIR protocol or definition."
    )
    instantiatesUri: list[str] | None = Field(
        None, description="Instantiates external protocol or definition."
    )
    basedOn: list[FHIRReference] | None = Field(
        None, description="What request fulfills."
    )
    groupIdentifier: FHIRIdentifier | None = Field(
        None, description="Composite request this is part of."
    )
    courseOfTherapyType: FHIRCodeableConcept | None = Field(
        None, description="Overall pattern of medication administration."
    )
    insurance: list[FHIRReference] | None = Field(
        None, description="Associated insurance coverage."
    )
    note: list[FHIRAnnotation] | None = Field(
        None, description="Information about the prescription."
    )
    dosageInstruction: list[FHIRDosage] | None = Field(
        None, description="How the medication should be taken."
    )
    dispenseRequest: FHIRMedicationRequestDispenseRequest | None = Field(
        None, description="Medication supply authorization."
    )
    substitution: FHIRMedicationRequestSubstitution | None = Field(
        None, description="Any restrictions on medication substitution."
    )
    priorPrescription: FHIRReference | None = Field(
        None, description="An order/prescription that is being replaced."
    )
    detectedIssue: list[FHIRReference] | None = Field(
        None, description="Clinical Issue with action."
    )
    eventHistory: list[FHIRReference] | None = Field(
        None, description="A list of events of interest in the lifecycle."
    )


class FHIRMedicationRequestBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRMedicationRequestSchema | dict = Field(
        ...,
        description="A MedicationRequest (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Encounter / Medication / Practitioner / PractitionerRole / RelatedPerson / Organization (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRMedicationRequestBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRMedicationRequestBundleEntry] | None = None
