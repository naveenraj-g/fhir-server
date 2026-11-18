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
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink

from .qualification import FHIRPractitionerQualification


class FHIRPractitionerSchema(BaseModel):
    resourceType: str = Field("Practitioner", description="Always 'Practitioner'.")
    id: str = Field(..., description="Public practitioner_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — includes the user-id extension when the record belongs to an end-user.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="An identifier for the person as this agent."
    )
    active: bool | None = Field(
        None, description="Whether this practitioner's record is in active use."
    )
    name: list[FHIRHumanName] | None = Field(
        None, description="The name(s) associated with the practitioner."
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None, description="A contact detail for the practitioner (that apply to all roles)."
    )
    address: list[FHIRAddress] | None = Field(
        None, description="Address(es) of the practitioner that are not role specific."
    )
    gender: str | None = Field(None, description="male | female | other | unknown.")
    birthDate: str | None = Field(
        None, description="The date on which the practitioner was born."
    )
    photo: list[FHIRAttachment] | None = Field(None, description="Image of the person.")
    qualification: list[FHIRPractitionerQualification] | None = Field(
        None, description="Certification, licenses, or training pertaining to the provision of care."
    )
    communication: list[FHIRCodeableConcept] | None = Field(
        None, description="A language the practitioner can use in patient communication."
    )


class FHIRPractitionerBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRPractitionerSchema | dict = Field(
        ...,
        description="A Practitioner (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED) or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRPractitionerBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages. Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRPractitionerBundleEntry] | None = None
