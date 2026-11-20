from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRQuantity,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRImmunizationAnnotation(BaseModel):
    authorReference: FHIRReference | None = Field(None, description="Individual responsible for the annotation.")
    authorString: str | None = Field(None, description="Individual responsible for the annotation, as plain text.")
    time: str | None = Field(None, description="When the annotation was made.")
    text: str | None = Field(None, description="The annotation text.")


class FHIRImmunizationPerformer(BaseModel):
    function: FHIRCodeableConcept | None = Field(None, description="What type of performance was done.")
    actor: FHIRReference | None = Field(None, description="Individual or organization who was performing.")


class FHIRImmunizationEducation(BaseModel):
    documentType: str | None = Field(None, description="Educational material document identifier.")
    reference: str | None = Field(None, description="Educational material reference pointer.")
    publicationDate: str | None = Field(None, description="Educational material publication date.")
    presentationDate: str | None = Field(None, description="Educational material presentation date.")


class FHIRImmunizationReaction(BaseModel):
    date: str | None = Field(None, description="When the reaction started.")
    detail: FHIRReference | None = Field(None, description="Additional information on the reaction.")
    reported: bool | None = Field(None, description="Indicates a self-reported reaction.")


class FHIRImmunizationProtocolApplied(BaseModel):
    series: str | None = Field(None, description="Name of the vaccine series.")
    authority: FHIRReference | None = Field(None, description="Who is responsible for publishing the recommendations.")
    targetDisease: list[FHIRCodeableConcept] | None = Field(None, description="Vaccine preventable disease being targeted.")
    doseNumberPositiveInt: int | None = Field(None, description="Dose number within the series.")
    doseNumberString: str | None = Field(None, description="Dose number within the series (string).")
    seriesDosesPositiveInt: int | None = Field(None, description="Recommended number of doses for immunity.")
    seriesDosesString: str | None = Field(None, description="Recommended number of doses for immunity (string).")


class FHIRImmunizationSchema(BaseModel):
    resourceType: str = Field("Immunization", description="Always 'Immunization'.")
    id: str = Field(..., description="Public immunization_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries."
    )
    identifier: list[FHIRIdentifier] | None = Field(None, description="Business identifier.")
    status: str | None = Field(None, description="completed | entered-in-error | not-done.")
    statusReason: FHIRCodeableConcept | None = Field(None, description="Reason not done.")
    vaccineCode: FHIRCodeableConcept | None = Field(None, description="Vaccine product administered.")
    patient: FHIRReference | None = Field(None, description="Who was immunized.")
    encounter: FHIRReference | None = Field(None, description="Encounter immunization was part of.")
    occurrenceDateTime: str | None = Field(None, description="Vaccine administration date.")
    occurrenceString: str | None = Field(None, description="Vaccine administration date (string).")
    recorded: str | None = Field(None, description="When the immunization was first captured in the subject's record.")
    primarySource: bool | None = Field(None, description="Indicates the context the data was recorded in.")
    reportOrigin: FHIRCodeableConcept | None = Field(None, description="Indicates the source of a secondarily reported record.")
    location: FHIRReference | None = Field(None, description="Where the immunization occurred.")
    manufacturer: FHIRReference | None = Field(None, description="Vaccine manufacturer.")
    lotNumber: str | None = Field(None, description="Vaccine lot number.")
    expirationDate: str | None = Field(None, description="Vaccine expiration date.")
    site: FHIRCodeableConcept | None = Field(None, description="Body site vaccine was administered.")
    route: FHIRCodeableConcept | None = Field(None, description="How the vaccine entered the body.")
    doseQuantity: FHIRQuantity | None = Field(None, description="Amount of vaccine administered.")
    performer: list[FHIRImmunizationPerformer] | None = Field(None, description="Who performed the event.")
    note: list[FHIRImmunizationAnnotation] | None = Field(None, description="Additional immunization notes.")
    reasonCode: list[FHIRCodeableConcept] | None = Field(None, description="Why the immunization occurred.")
    reasonReference: list[FHIRReference] | None = Field(None, description="Why the immunization occurred.")
    isSubpotent: bool | None = Field(None, description="Dose potency.")
    subpotentReason: list[FHIRCodeableConcept] | None = Field(None, description="Reason for being subpotent.")
    education: list[FHIRImmunizationEducation] | None = Field(None, description="Educational material presented to the patient.")
    programEligibility: list[FHIRCodeableConcept] | None = Field(None, description="Patient eligibility for a vaccination program.")
    fundingSource: FHIRCodeableConcept | None = Field(None, description="Funding source for the vaccine.")
    reaction: list[FHIRImmunizationReaction] | None = Field(None, description="Details of a reaction that follows immunization.")
    protocolApplied: list[FHIRImmunizationProtocolApplied] | None = Field(None, description="Protocol followed by the provider.")


class FHIRImmunizationBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRImmunizationSchema | dict = Field(
        ...,
        description="An Immunization (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Location / Organization / Practitioner / PractitionerRole / Condition / DiagnosticReport (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRImmunizationBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRImmunizationBundleEntry] | None = None
