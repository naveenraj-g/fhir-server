from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRScheduleSchema(BaseModel):
    resourceType: str = Field("Schedule", description="Always 'Schedule'.")
    id: str = Field(..., description="Public schedule_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External Ids for this item."
    )
    active: bool | None = Field(
        None, description="Whether this schedule is in active use."
    )
    serviceCategory: list[FHIRCodeableConcept] | None = Field(
        None, description="High-level category."
    )
    serviceType: list[FHIRCodeableConcept] | None = Field(
        None, description="Specific service."
    )
    specialty: list[FHIRCodeableConcept] | None = Field(
        None, description="Type of specialty needed."
    )
    actor: list[FHIRReference] | None = Field(
        None,
        description="Resource(s) that availability information is being provided for.",
    )
    planningHorizon: FHIRPeriod | None = Field(
        None, description="Period of time covered by schedule."
    )
    comment: str | None = Field(None, description="Comments on availability.")


class FHIRScheduleBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRScheduleSchema | dict = Field(
        ...,
        description="A Schedule (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource of another type (a Practitioner, PractitionerRole, HealthcareService or Location actor from _include), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRScheduleBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRScheduleBundleEntry] | None = None
