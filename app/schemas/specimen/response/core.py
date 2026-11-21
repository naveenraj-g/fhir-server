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
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRSpecimenAnnotation(BaseModel):
    authorReference: FHIRReference | None = Field(
        None, description="Individual responsible for the annotation."
    )
    authorString: str | None = Field(
        None, description="Individual responsible for the annotation, as plain text."
    )
    time: str | None = Field(None, description="When the annotation was made.")
    text: str | None = Field(None, description="The annotation text.")


class FHIRSpecimenCollection(BaseModel):
    collector: FHIRReference | None = Field(
        None, description="Who collected the specimen."
    )
    collectedDateTime: str | None = Field(
        None, description="Collection time (dateTime)."
    )
    collectedPeriod: FHIRPeriod | None = Field(
        None, description="Collection time (Period)."
    )
    duration: FHIRQuantity | None = Field(
        None, description="How long it took to collect specimen."
    )
    quantity: FHIRQuantity | None = Field(
        None, description="The quantity of specimen collected."
    )
    method: FHIRCodeableConcept | None = Field(
        None, description="Technique used to perform collection."
    )
    bodySite: FHIRCodeableConcept | None = Field(
        None, description="Anatomical collection site."
    )
    fastingStatusCodeableConcept: FHIRCodeableConcept | None = Field(
        None,
        description="Whether or how long patient abstained from food and/or drink (CodeableConcept).",
    )
    fastingStatusDuration: FHIRQuantity | None = Field(
        None,
        description="Whether or how long patient abstained from food and/or drink (Duration).",
    )


class FHIRSpecimenProcessing(BaseModel):
    description: str | None = Field(
        None, description="Textual description of procedure."
    )
    procedure: FHIRCodeableConcept | None = Field(
        None, description="Indicates the treatment step applied to the specimen."
    )
    additive: list[FHIRReference] | None = Field(
        None, description="Material used in the processing step."
    )
    timeDateTime: str | None = Field(
        None, description="Date and time of specimen processing (dateTime)."
    )
    timePeriod: FHIRPeriod | None = Field(
        None, description="Date and time of specimen processing (Period)."
    )


class FHIRSpecimenContainer(BaseModel):
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Id for the container."
    )
    description: str | None = Field(
        None, description="Textual description of the container."
    )
    type: FHIRCodeableConcept | None = Field(
        None, description="Kind of container directly associated with specimen."
    )
    capacity: FHIRQuantity | None = Field(None, description="Container volume or size.")
    specimenQuantity: FHIRQuantity | None = Field(
        None, description="Quantity of specimen within container."
    )
    additiveCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="Additive associated with container (CodeableConcept)."
    )
    additiveReference: FHIRReference | None = Field(
        None, description="Additive associated with container (Reference)."
    )


class FHIRSpecimenSchema(BaseModel):
    resourceType: str = Field("Specimen", description="Always 'Specimen'.")
    id: str = Field(..., description="Public specimen_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External Identifier."
    )
    accessionIdentifier: FHIRIdentifier | None = Field(
        None, description="Identifier assigned by the lab."
    )
    status: str | None = Field(
        None, description="available | unavailable | unsatisfactory | entered-in-error."
    )
    type: FHIRCodeableConcept | None = Field(
        None, description="Kind of material that forms the specimen."
    )
    subject: FHIRReference | None = Field(
        None, description="Where the specimen came from."
    )
    receivedTime: str | None = Field(
        None, description="The time when specimen was received for processing."
    )
    parent: list[FHIRReference] | None = Field(
        None, description="Specimen from which this specimen originated."
    )
    request: list[FHIRReference] | None = Field(
        None, description="Why the specimen was collected."
    )
    collection: FHIRSpecimenCollection | None = Field(
        None, description="Collection details."
    )
    processing: list[FHIRSpecimenProcessing] | None = Field(
        None, description="Processing and processing step details."
    )
    container: list[FHIRSpecimenContainer] | None = Field(
        None, description="Direct container of specimen (tube/slide, etc.)."
    )
    condition: list[FHIRCodeableConcept] | None = Field(
        None, description="State of the specimen."
    )
    note: list[FHIRSpecimenAnnotation] | None = Field(None, description="Comments.")


class FHIRSpecimenBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRSpecimenSchema | dict = Field(
        ...,
        description="A Specimen (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Location / Practitioner / PractitionerRole / Specimen (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRSpecimenBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRSpecimenBundleEntry] | None = None
