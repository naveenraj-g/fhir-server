from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRQuantity,
    FHIRRange,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRServiceRequestAnnotation(BaseModel):
    authorReference: FHIRReference | None = Field(
        None, description="Individual responsible for the annotation."
    )
    authorString: str | None = Field(
        None, description="Individual responsible for the annotation, as plain text."
    )
    time: str | None = Field(None, description="When the annotation was made.")
    text: str | None = Field(None, description="The annotation text.")


class FHIRServiceRequestRatio(BaseModel):
    numerator: FHIRQuantity | None = Field(None, description="Numerator value.")
    denominator: FHIRQuantity | None = Field(None, description="Denominator value.")


class FHIRServiceRequestSchema(BaseModel):
    resourceType: str = Field("ServiceRequest", description="Always 'ServiceRequest'.")
    id: str = Field(..., description="Public service_request_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Identifiers assigned to this order."
    )
    instantiatesCanonical: list[str] | None = Field(
        None, description="Instantiates FHIR protocol or definition (canonical URLs)."
    )
    instantiatesUri: list[str] | None = Field(
        None, description="Instantiates external protocol or definition."
    )
    basedOn: list[FHIRReference] | None = Field(
        None, description="What request fulfills."
    )
    replaces: list[FHIRReference] | None = Field(
        None, description="What request replaces."
    )
    requisition: FHIRIdentifier | None = Field(
        None, description="Composite Request ID."
    )
    status: str | None = Field(
        None,
        description="draft | active | on-hold | revoked | completed | entered-in-error | unknown.",
    )
    intent: str | None = Field(
        None,
        description="proposal | plan | directive | order | original-order | reflex-order | filler-order | instance-order | option.",
    )
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="Classification of service."
    )
    priority: str | None = Field(None, description="routine | urgent | asap | stat.")
    doNotPerform: bool | None = Field(
        None, description="True if the service should NOT be performed."
    )
    code: FHIRCodeableConcept | None = Field(
        None, description="What is being requested/ordered."
    )
    orderDetail: list[FHIRCodeableConcept] | None = Field(
        None, description="Additional order information."
    )
    quantityQuantity: FHIRQuantity | None = Field(
        None, description="Service amount (Quantity)."
    )
    quantityRatio: FHIRServiceRequestRatio | None = Field(
        None, description="Service amount (Ratio)."
    )
    quantityRange: FHIRRange | None = Field(None, description="Service amount (Range).")
    subject: FHIRReference | None = Field(
        None, description="Individual or entity the service is ordered for."
    )
    encounter: FHIRReference | None = Field(
        None, description="Encounter in which the request was created."
    )
    occurrenceDateTime: str | None = Field(
        None, description="When service should occur (dateTime)."
    )
    occurrencePeriod: FHIRPeriod | None = Field(
        None, description="When service should occur (Period)."
    )
    occurrenceTiming: dict | None = Field(
        None, description="When service should occur (Timing)."
    )
    asNeededBoolean: bool | None = Field(
        None, description="Preconditions for service (boolean)."
    )
    asNeededCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="Preconditions for service (CodeableConcept)."
    )
    authoredOn: str | None = Field(None, description="Date request signed.")
    requester: FHIRReference | None = Field(
        None, description="Who/what is requesting service."
    )
    performerType: FHIRCodeableConcept | None = Field(
        None, description="Performer role."
    )
    performer: list[FHIRReference] | None = Field(
        None, description="Requested performer."
    )
    locationCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Requested location (coded)."
    )
    locationReference: list[FHIRReference] | None = Field(
        None, description="Requested location."
    )
    reasonCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Explanation/justification (coded)."
    )
    reasonReference: list[FHIRReference] | None = Field(
        None, description="Explanation/justification."
    )
    insurance: list[FHIRReference] | None = Field(
        None, description="Associated insurance coverage."
    )
    supportingInfo: list[FHIRReference] | None = Field(
        None, description="Additional clinical information."
    )
    specimen: list[FHIRReference] | None = Field(None, description="Procedure samples.")
    bodySite: list[FHIRCodeableConcept] | None = Field(
        None, description="Location on Body."
    )
    note: list[FHIRServiceRequestAnnotation] | None = Field(
        None, description="Comments."
    )
    patientInstruction: str | None = Field(
        None, description="Patient or consumer-oriented instructions."
    )
    relevantHistory: list[FHIRReference] | None = Field(
        None, description="Request provenance."
    )


class FHIRServiceRequestBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRServiceRequestSchema | dict = Field(
        ...,
        description="A ServiceRequest (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Location / Encounter / Practitioner / PractitionerRole / RelatedPerson / Organization / HealthcareService / Specimen / ServiceRequest (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRServiceRequestBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRServiceRequestBundleEntry] | None = None
