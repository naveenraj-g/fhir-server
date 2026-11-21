from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRAddress,
    FHIRAttachment,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRHumanName,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRRelatedPersonCommunication(BaseModel):
    language: FHIRCodeableConcept | None = Field(
        None,
        description="The language which can be used to communicate with the related person.",
    )
    preferred: bool | None = Field(None, description="Language preference indicator.")


class FHIRRelatedPersonSchema(BaseModel):
    resourceType: str = Field("RelatedPerson", description="Always 'RelatedPerson'.")
    id: str = Field(..., description="Public related_person_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="A human identifier for this person."
    )
    active: bool | None = Field(
        None, description="Whether this related person record is in active use."
    )
    patient: FHIRReference | None = Field(
        None, description="The patient this person is related to."
    )
    relationship: list[FHIRCodeableConcept] | None = Field(
        None, description="The nature of the relationship."
    )
    name: list[FHIRHumanName] | None = Field(
        None, description="A name associated with the person."
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None, description="A contact detail for the person."
    )
    gender: str | None = Field(None, description="male | female | other | unknown.")
    birthDate: str | None = Field(
        None, description="The date on which the related person was born."
    )
    address: list[FHIRAddress] | None = Field(
        None,
        description="Address where the related person can be contacted or visited.",
    )
    photo: list[FHIRAttachment] | None = Field(None, description="Image of the person.")
    period: FHIRPeriod | None = Field(
        None, description="Period of time that this relationship is considered valid."
    )
    communication: list[FHIRRelatedPersonCommunication] | None = Field(
        None,
        description="A language which may be used to communicate with about the patient health.",
    )


class FHIRRelatedPersonBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRRelatedPersonSchema | dict = Field(
        ...,
        description="A RelatedPerson (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / RelatedPerson (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRRelatedPersonBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRRelatedPersonBundleEntry] | None = None
