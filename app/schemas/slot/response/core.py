from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRSlotSchema(BaseModel):
    resourceType: str = Field("Slot", description="Always 'Slot'.")
    id: str = Field(..., description="Public slot_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries."
    )
    identifier: list[FHIRIdentifier] | None = Field(None, description="External Ids for this item.")
    serviceCategory: list[FHIRCodeableConcept] | None = Field(None, description="A broad categorization of the service that is to be performed during this appointment.")
    serviceType: list[FHIRCodeableConcept] | None = Field(None, description="The type of appointments that can be booked into this slot.")
    specialty: list[FHIRCodeableConcept] | None = Field(None, description="The specialty of a practitioner that would be required to perform the service requested in this appointment.")
    appointmentType: FHIRCodeableConcept | None = Field(None, description="The style of appointment or patient that may be booked in the slot (not service type).")
    schedule: FHIRReference | None = Field(None, description="The schedule resource that this slot defines an interval of status information.")
    status: str | None = Field(None, description="busy | free | busy-unavailable | busy-tentative | entered-in-error.")
    start: str | None = Field(None, description="Date/Time that the slot is to begin.")
    end: str | None = Field(None, description="Date/Time that the slot is to conclude.")
    overbooked: bool | None = Field(None, description="This slot has already been overbooked, appointments are unlikely to be accepted for this time.")
    comment: str | None = Field(None, description="Comments on the slot to describe any extended information.")


class FHIRSlotBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRSlotSchema | dict = Field(
        ...,
        description="A Slot (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Schedule (from _include=Slot:schedule), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRSlotBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRSlotBundleEntry] | None = None
