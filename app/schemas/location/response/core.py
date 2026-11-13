from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRAddress,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRCoding,
    FHIRContactPoint,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)

from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink

# ── FHIR (camelCase) ───────────────────────────────────────────────────────────


class FHIRLocationPosition(BaseModel):
    """Location.position — the absolute geographic location (BackboneElement)."""

    longitude: Decimal | None = Field(None, description="Longitude with WGS84 datum.")
    latitude: Decimal | None = Field(None, description="Latitude with WGS84 datum.")
    altitude: Decimal | None = Field(None, description="Altitude with WGS84 datum.")


class FHIRLocationHoursOfOperation(BaseModel):
    """Location.hoursOfOperation — what days/times during a week the location is
    generally open (BackboneElement)."""

    daysOfWeek: list[str] | None = Field(
        None,
        description="Indicates which days of the week are available between the start and end times.",
    )
    allDay: bool | None = Field(
        None, description="The Location is open all day (24 hours)."
    )
    openingTime: str | None = Field(
        None, description="Time that the Location opens."
    )
    closingTime: str | None = Field(
        None, description="Time that the Location closes."
    )


class FHIRLocationSchema(BaseModel):
    resourceType: str = Field("Location", description="Always 'Location'.")
    id: str = Field(..., description="Public location_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries. Not yet validated against registered extension definitions.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Unique code or number identifying the location to its users."
    )
    status: str | None = Field(
        None,
        description="The status of the location as normally viewed by a user — active|suspended|inactive.",
    )
    operationalStatus: FHIRCoding | None = Field(
        None,
        description="The operational status of the location (typically only for a bed/room).",
    )
    name: str | None = Field(
        None, description="Name of the location as used by humans."
    )
    alias: list[str] | None = Field(
        None,
        description="A list of alternate names that the location is known as, or was known as, in the past.",
    )
    description: str | None = Field(
        None,
        description="Additional details about the location that could be displayed as further information to identify the location beyond its name.",
    )
    mode: str | None = Field(
        None,
        description="Indicates whether a resource instance represents a specific location or a class of locations — instance|kind.",
    )
    type: list[FHIRCodeableConcept] | None = Field(
        None, description="Indicates the type of function performed at the location."
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None,
        description="The contact details of communication devices available at the location.",
    )
    address: FHIRAddress | None = Field(
        None,
        description="Physical location. Singular (0..1) in FHIR R4 — unlike Organization.address, which repeats.",
    )
    physicalType: FHIRCodeableConcept | None = Field(
        None, description="Physical form of the location, e.g. building, room, vehicle."
    )
    position: FHIRLocationPosition | None = Field(
        None,
        description="The absolute geographic location of the Location, expressed using the WGS84 datum.",
    )
    managingOrganization: FHIRReference | None = Field(
        None,
        description="The organization responsible for the provisioning and upkeep of the location.",
    )
    partOf: FHIRReference | None = Field(
        None,
        description="Another Location of which this Location is physically a part of.",
    )
    hoursOfOperation: list[FHIRLocationHoursOfOperation] | None = Field(
        None, description="What days/times during a week is this location usually open."
    )
    availabilityExceptions: str | None = Field(
        None,
        description="A description of when the locations opening ours are different to normal.",
    )
    endpoint: list[FHIRReference] | None = Field(
        None,
        description="Technical endpoints providing access to services operated for the location.",
    )


class FHIRLocationBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRLocationSchema | dict = Field(
        ...,
        description="A Location (match/include; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource of another type (e.g. the managing Organization from _include=Location:organization), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRLocationBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRLocationBundleEntry] | None = None
