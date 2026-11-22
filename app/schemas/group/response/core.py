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


class FHIRGroupCharacteristic(BaseModel):
    code: FHIRCodeableConcept | None = Field(
        None, description="Kind of characteristic."
    )
    valueCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="Value held by characteristic (CodeableConcept)."
    )
    valueBoolean: bool | None = Field(
        None, description="Value held by characteristic (boolean)."
    )
    valueQuantity: FHIRQuantity | None = Field(
        None, description="Value held by characteristic (Quantity)."
    )
    valueRange: FHIRRange | None = Field(
        None, description="Value held by characteristic (Range)."
    )
    valueReference: FHIRReference | None = Field(
        None, description="Value held by characteristic (Reference)."
    )
    exclude: bool | None = Field(None, description="Group includes or excludes.")
    period: FHIRPeriod | None = Field(
        None, description="Period over which characteristic is tested."
    )


class FHIRGroupMember(BaseModel):
    entity: FHIRReference | None = Field(
        None, description="Reference to the group member."
    )
    period: FHIRPeriod | None = Field(
        None, description="Period member belonged to the group."
    )
    inactive: bool | None = Field(None, description="If member is no longer in group.")


class FHIRGroupSchema(BaseModel):
    resourceType: str = Field("Group", description="Always 'Group'.")
    id: str = Field(..., description="Public group_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(None, description="Unique id.")
    active: bool | None = Field(
        None, description="Whether this group's record is in active use."
    )
    type: str | None = Field(
        None,
        description="person | animal | practitioner | device | medication | substance.",
    )
    actual: bool | None = Field(
        None, description="Descriptive (false) or actual (true)."
    )
    code: FHIRCodeableConcept | None = Field(None, description="Kind of Group members.")
    name: str | None = Field(None, description="Label for Group.")
    quantity: int | None = Field(None, description="Number of members.")
    managingEntity: FHIRReference | None = Field(
        None, description="Entity that is the custodian of the Group's definition."
    )
    characteristic: list[FHIRGroupCharacteristic] | None = Field(
        None, description="Include / Exclude group members by Trait."
    )
    member: list[FHIRGroupMember] | None = Field(
        None, description="Who or what is in group."
    )


class FHIRGroupBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRGroupSchema | dict = Field(
        ...,
        description="A Group (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Organization / RelatedPerson / Practitioner / PractitionerRole / Patient / Medication / Group (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRGroupBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRGroupBundleEntry] | None = None
