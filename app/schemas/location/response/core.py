from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common.fhir import (
    FHIRAddress,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRCoding,
    FHIRContactPoint,
    FHIRIdentifier,
    FHIRReference,
)

from .alias import PlainLocationAlias
from .endpoint import PlainLocationEndpoint
from .hours_of_operation import PlainLocationHoursOfOperation
from .identifier import PlainLocationIdentifier
from .telecom import PlainLocationTelecom
from .type import PlainLocationType

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
    resource: FHIRLocationSchema


class FHIRLocationBundle(FHIRBundle):
    entry: list[FHIRLocationBundleEntry] | None = None


# ── Plain (snake_case) ─────────────────────────────────────────────────────────


class PlainLocationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public location_id.")
    status: str | None = Field(
        None,
        description="The status of the location as normally viewed by a user — active|suspended|inactive.",
    )
    operational_status_system: str | None = Field(
        None, description="Operational status — the code system for the code."
    )
    operational_status_version: str | None = Field(
        None, description="Operational status — the version of the code system."
    )
    operational_status_code: str | None = Field(
        None, description="Operational status — a symbol defined by the code system."
    )
    operational_status_display: str | None = Field(
        None, description="Operational status — the meaning of the code in the system."
    )
    operational_status_user_selected: bool | None = Field(
        None, description="Operational status — whether the coding was user-selected."
    )
    name: str | None = Field(
        None, description="Name of the location as used by humans."
    )
    description: str | None = Field(
        None, description="Description of the Location."
    )
    mode: str | None = Field(
        None,
        description="Whether this record describes a specific instance of a location, or a class of locations — instance|kind.",
    )

    address_use: str | None = Field(None, description="The purpose of this address.")
    address_type: str | None = Field(
        None, description="postal|physical|both."
    )
    address_text: str | None = Field(
        None, description="A full text representation of the address."
    )
    address_line: list[str] | None = Field(
        None,
        description="Street name, number, direction, PO Box etc. Split back out from the comma-separated column by the mapper.",
    )
    address_city: str | None = Field(None, description="City, town or village.")
    address_district: str | None = Field(
        None, description="The name of the administrative area (county)."
    )
    address_state: str | None = Field(None, description="Sub-unit of a country.")
    address_postal_code: str | None = Field(None, description="Postal code.")
    address_country: str | None = Field(None, description="Country.")
    address_period_start: str | None = Field(
        None, description="Start of the time period when this address was/is in use."
    )
    address_period_end: str | None = Field(
        None, description="End of the time period when this address was/is in use."
    )

    physical_type_system: str | None = Field(
        None, description="Physical form — the code system for the code."
    )
    physical_type_version: str | None = Field(
        None, description="Physical form — the version of the code system."
    )
    physical_type_code: str | None = Field(
        None, description="Physical form — a symbol defined by the code system."
    )
    physical_type_display: str | None = Field(
        None, description="Physical form — the meaning of the code in the system."
    )
    physical_type_text: str | None = Field(
        None, description="Physical form — a human language representation."
    )
    physical_type_user_selected: bool | None = Field(
        None, description="Physical form — whether the coding was user-selected."
    )

    position_longitude: Decimal | None = Field(
        None, description="Longitude with WGS84 datum."
    )
    position_latitude: Decimal | None = Field(
        None, description="Latitude with WGS84 datum."
    )
    position_altitude: Decimal | None = Field(
        None, description="Altitude with WGS84 datum."
    )

    managing_organization: str | None = Field(
        None,
        description="Resolved FHIR reference to the managing organization, e.g. 'Organization/190001'.",
    )
    managing_organization_type: str | None = Field(
        None, description="Resolved reference target type (always 'Organization')."
    )
    managing_organization_id: int | None = Field(
        None, description="Public ID of the resolved managing Organization, if any."
    )
    managing_organization_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the managing organization.",
    )
    managing_organization_identifier_use: str | None = Field(
        None, description="Fallback identifier — its purpose, if known."
    )
    managing_organization_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — code system for its type."
    )
    managing_organization_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type code system."
    )
    managing_organization_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    managing_organization_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    managing_organization_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )
    managing_organization_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — whether its type was user-selected."
    )
    managing_organization_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    managing_organization_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    managing_organization_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    managing_organization_identifier_period_end: str | None = Field(
        None, description="Fallback identifier — end of validity period."
    )

    part_of: str | None = Field(
        None,
        description="Resolved FHIR reference to the containing location, e.g. 'Location/230001'.",
    )
    part_of_type: str | None = Field(
        None, description="Resolved reference target type (always 'Location')."
    )
    part_of_id: int | None = Field(
        None, description="Public ID of the resolved containing Location, if any."
    )
    part_of_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the containing location.",
    )
    part_of_identifier_use: str | None = Field(
        None, description="Fallback identifier — its purpose, if known."
    )
    part_of_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — code system for its type."
    )
    part_of_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type code system."
    )
    part_of_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    part_of_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    part_of_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )
    part_of_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — whether its type was user-selected."
    )
    part_of_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    part_of_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    part_of_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    part_of_identifier_period_end: str | None = Field(
        None, description="Fallback identifier — end of validity period."
    )

    availability_exceptions: str | None = Field(
        None,
        description="A description of when the locations opening ours are different to normal.",
    )

    identifier: list[PlainLocationIdentifier] | None = Field(
        None, description="Unique code or number identifying the location to its users."
    )
    type: list[PlainLocationType] | None = Field(
        None, description="Indicates the type of function performed at the location."
    )
    alias: list[PlainLocationAlias] | None = Field(
        None,
        description="A list of alternate names that the location is known as, or was known as, in the past.",
    )
    telecom: list[PlainLocationTelecom] | None = Field(
        None,
        description="The contact details of communication devices available at the location.",
    )
    hours_of_operation: list[PlainLocationHoursOfOperation] | None = Field(
        None, description="What days/times during a week is this location usually open."
    )
    endpoint: list[PlainLocationEndpoint] | None = Field(
        None,
        description="Technical endpoints providing access to services operated for the location.",
    )

    org_id: str | None = Field(
        None,
        description="ID of the tenant/account this record is scoped to (multi-tenancy), taken from the verified JWT's activeOrganizationId — not a FHIR concept, and unrelated to managing_organization.",
    )
    created_at: str | None = Field(None, description="When this row was created.")
    updated_at: str | None = Field(None, description="When this row was last updated.")
    created_by: str | None = Field(
        None,
        description="Acting user who created this record, taken from the verified JWT's sub.",
    )
    updated_by: str | None = Field(
        None,
        description="Acting user who last updated this record, taken from the verified JWT's sub.",
    )


class PaginatedLocationResponse(BaseModel):
    total: int | None = Field(
        None, description="Total matching rows (null when total_mode=none)."
    )
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Number of rows skipped before this page.")
    data: list[PlainLocationResponse]
