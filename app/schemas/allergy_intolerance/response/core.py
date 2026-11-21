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


class FHIRAllergyIntoleranceAnnotation(BaseModel):
    authorReference: FHIRReference | None = Field(
        None, description="Individual responsible for the annotation."
    )
    authorString: str | None = Field(
        None, description="Individual responsible for the annotation, as plain text."
    )
    time: str | None = Field(None, description="When the annotation was made.")
    text: str | None = Field(None, description="The annotation text.")


class FHIRAllergyIntoleranceReaction(BaseModel):
    substance: FHIRCodeableConcept | None = Field(
        None,
        description="Specific substance or pharmaceutical product considered to be responsible for the event.",
    )
    manifestation: list[FHIRCodeableConcept] | None = Field(
        None, description="Clinical symptoms/signs associated with the event."
    )
    description: str | None = Field(
        None, description="Description of the event as a whole."
    )
    onset: str | None = Field(
        None, description="Date(/time) when manifestations showed."
    )
    severity: str | None = Field(
        None, description="mild | moderate | severe (of event as a whole)."
    )
    exposureRoute: FHIRCodeableConcept | None = Field(
        None, description="How the subject was exposed to the substance."
    )
    note: list[FHIRAllergyIntoleranceAnnotation] | None = Field(
        None, description="Text about event not captured in other fields."
    )


class FHIRAllergyIntoleranceSchema(BaseModel):
    resourceType: str = Field(
        "AllergyIntolerance", description="Always 'AllergyIntolerance'."
    )
    id: str = Field(..., description="Public allergy_intolerance_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External ids for this item."
    )
    clinicalStatus: FHIRCodeableConcept | None = Field(
        None, description="active | inactive | resolved."
    )
    verificationStatus: FHIRCodeableConcept | None = Field(
        None, description="unconfirmed | confirmed | refuted | entered-in-error."
    )
    type: str | None = Field(
        None, description="allergy | intolerance - Underlying mechanism (if known)."
    )
    category: list[str] | None = Field(
        None, description="food | medication | environment | biologic."
    )
    criticality: str | None = Field(None, description="low | high | unable-to-assess.")
    code: FHIRCodeableConcept | None = Field(
        None, description="Code that identifies the allergy or intolerance."
    )
    patient: FHIRReference | None = Field(
        None, description="Who the sensitivity is for."
    )
    encounter: FHIRReference | None = Field(
        None, description="Encounter when the allergy or intolerance was asserted."
    )
    onsetDateTime: str | None = Field(
        None, description="When allergy or intolerance was identified."
    )
    onsetAge: FHIRQuantity | None = Field(
        None, description="When allergy or intolerance was identified (Age)."
    )
    onsetPeriod: FHIRPeriod | None = Field(
        None, description="When allergy or intolerance was identified (Period)."
    )
    onsetRange: FHIRRange | None = Field(
        None, description="When allergy or intolerance was identified (Range)."
    )
    onsetString: str | None = Field(
        None, description="When allergy or intolerance was identified (text)."
    )
    recordedDate: str | None = Field(
        None, description="Date first version of the resource instance was recorded."
    )
    recorder: FHIRReference | None = Field(
        None, description="Who recorded the sensitivity."
    )
    asserter: FHIRReference | None = Field(
        None, description="Source of the information about the allergy."
    )
    lastOccurrence: str | None = Field(
        None, description="Date(/time) of last known occurrence of a reaction."
    )
    note: list[FHIRAllergyIntoleranceAnnotation] | None = Field(
        None, description="Additional text not captured in other fields."
    )
    reaction: list[FHIRAllergyIntoleranceReaction] | None = Field(
        None, description="Adverse Reaction Events linked to exposure to substance."
    )


class FHIRAllergyIntoleranceBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRAllergyIntoleranceSchema | dict = Field(
        ...,
        description="An AllergyIntolerance (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Practitioner / PractitionerRole / RelatedPerson (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRAllergyIntoleranceBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRAllergyIntoleranceBundleEntry] | None = None
