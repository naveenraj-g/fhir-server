from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)
from app.schemas.datatypes.annotation import FHIRAnnotation
from app.schemas.datatypes.dosage import FHIRDosage
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRMedicationDispensePerformer(BaseModel):
    function: FHIRCodeableConcept | None = Field(
        None, description="Who performed the dispense and what they did."
    )
    actor: FHIRReference | None = Field(
        None, description="Individual who was performing."
    )


class FHIRMedicationDispenseSubstitution(BaseModel):
    wasSubstituted: bool | None = Field(
        None, description="Whether a substitution was or was not performed."
    )
    type: FHIRCodeableConcept | None = Field(
        None, description="Code signifying whether a different drug was dispensed."
    )
    reason: list[FHIRCodeableConcept] | None = Field(
        None, description="Why was substitution made."
    )
    responsibleParty: list[FHIRReference] | None = Field(
        None, description="Who is responsible for the substitution."
    )


class FHIRMedicationDispenseSchema(BaseModel):
    resourceType: str = Field(
        "MedicationDispense", description="Always 'MedicationDispense'."
    )
    id: str = Field(..., description="Public medication_dispense_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External identifier."
    )
    partOf: list[FHIRReference] | None = Field(
        None, description="Event that dispense is part of."
    )
    status: str | None = Field(
        None,
        description="preparation | in-progress | cancelled | on-hold | completed | entered-in-error | stopped | declined | unknown.",
    )
    statusReasonCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="Why a dispense was not performed (a CodeableConcept)."
    )
    statusReasonReference: FHIRReference | None = Field(
        None,
        description="Why a dispense was not performed (a Reference(DetectedIssue)).",
    )
    category: FHIRCodeableConcept | None = Field(
        None, description="Type of medication dispense."
    )
    medicationCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="What medication was supplied (a CodeableConcept)."
    )
    medicationReference: FHIRReference | None = Field(
        None, description="What medication was supplied (a Reference(Medication))."
    )
    subject: FHIRReference | None = Field(None, description="Who the dispense is for.")
    context: FHIRReference | None = Field(
        None, description="Encounter / Episode associated with event."
    )
    supportingInformation: list[FHIRReference] | None = Field(
        None, description="Information that supports the dispensing of the medication."
    )
    performer: list[FHIRMedicationDispensePerformer] | None = Field(
        None, description="Who performed event."
    )
    location: FHIRReference | None = Field(
        None, description="Where the dispense occurred."
    )
    authorizingPrescription: list[FHIRReference] | None = Field(
        None, description="Medication order that authorizes the dispense."
    )
    type: FHIRCodeableConcept | None = Field(
        None, description="Trial fill, partial fill, emergency fill, etc."
    )
    quantity: dict | None = Field(None, description="Amount dispensed.")
    daysSupply: dict | None = Field(
        None, description="Amount of medication expressed as a timing amount."
    )
    whenPrepared: str | None = Field(
        None, description="When product was packaged and reviewed."
    )
    whenHandedOver: str | None = Field(None, description="When product was given out.")
    destination: FHIRReference | None = Field(
        None, description="Where the medication was sent."
    )
    receiver: list[FHIRReference] | None = Field(
        None, description="Who collected the medication."
    )
    note: list[FHIRAnnotation] | None = Field(
        None, description="Information about the dispense."
    )
    dosageInstruction: list[FHIRDosage] | None = Field(
        None,
        description="How the medication is to be used by the patient or administered.",
    )
    substitution: FHIRMedicationDispenseSubstitution | None = Field(
        None, description="Whether a substitution was performed on the dispense."
    )
    detectedIssue: list[FHIRReference] | None = Field(
        None, description="Clinical issue with action."
    )
    eventHistory: list[FHIRReference] | None = Field(
        None, description="A list of relevant lifecycle events."
    )


class FHIRMedicationDispenseBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRMedicationDispenseSchema | dict = Field(
        ...,
        description="A MedicationDispense (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Group / Encounter / EpisodeOfCare / Location / Practitioner / PractitionerRole / Organization / RelatedPerson / Medication / MedicationRequest (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRMedicationDispenseBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRMedicationDispenseBundleEntry] | None = None
