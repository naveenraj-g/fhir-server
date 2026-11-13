from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirAddressInput,
    FhirCodeableConceptInput,
    FhirCodingInput,
    FhirContactPointInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirReferenceInput,
)

from .backbone import LocationHoursOfOperationInput, LocationPositionInput

_EXAMPLE = {
    "resourceType": "Location",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/location-ids",
            "value": "B1-S.F2",
        }
    ],
    "status": "active",
    "operationalStatus": {
        "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
        "code": "U",
        "display": "Unoccupied",
    },
    "name": "South Wing, second floor",
    "alias": ["BU MC, SW, F2", "Burgers University Medical Center, South Wing, second floor"],
    "description": "Second floor of the Old South Wing, formerly in use by Psychiatry",
    "mode": "instance",
    "type": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                    "code": "HOSP",
                    "display": "Hospital",
                }
            ]
        }
    ],
    "telecom": [{"system": "phone", "value": "2328", "use": "work"}],
    "address": {
        "use": "work",
        "line": ["Galapagosweg 91, Building A"],
        "city": "Den Burg",
        "postalCode": "9105 PZ",
        "country": "NLD",
    },
    "physicalType": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
                "code": "wi",
                "display": "Wing",
            }
        ]
    },
    "position": {"longitude": -83.6945691, "latitude": 42.25475478, "altitude": 0},
    "managingOrganization": {"reference": "Organization/190001"},
    "partOf": {"reference": "Location/230001", "display": "Burgers University Medical Center"},
    "hoursOfOperation": [
        {
            "daysOfWeek": ["mon", "tue", "wed", "thu", "fri"],
            "allDay": False,
            "openingTime": "09:00:00",
            "closingTime": "17:30:00",
        }
    ],
    "availabilityExceptions": "Reduced services on public holidays",
    "endpoint": [{"reference": "Endpoint/1"}],
}


class _LocationFields(FhirInputModel):
    """Every writable Location element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/location.html). Create and patch accept
    exactly the same fields — Location has no element required at this
    layer.

    The validated body is stored whole (LocationModel.content), so any valid
    R4 element is kept — including ones this model doesn't declare.
    Server-managed elements are ignored if sent: `id` (assigned from the
    location_id sequence) and `meta` (audit/tenant data, stamped on at read
    time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["Location"] | None = Field(
        None, description="Optional; if supplied it must be 'Location'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Unique code or number identifying the location to its users."
    )
    status: Literal["active", "suspended", "inactive"] | None = Field(
        None, description="active | suspended | inactive (required binding LocationStatus)."
    )
    operationalStatus: FhirCodingInput | None = Field(
        None,
        description="The operational status of the location (typically only for a bed/room), e.g. contaminated, housekeeping.",
    )
    name: str | None = Field(None, description="Name of the location as used by humans.")
    alias: list[str] | None = Field(
        None,
        description="A list of alternate names that the location is known as, or was known as, in the past.",
    )
    description: str | None = Field(
        None, description="Additional details about the location that could be displayed as further information."
    )
    mode: Literal["instance", "kind"] | None = Field(
        None,
        description="instance | kind — whether this is a specific place or a class of places (required binding LocationMode).",
    )
    type: list[FhirCodeableConceptInput] | None = Field(
        None, description="Type of function performed at the location."
    )
    telecom: list[FhirContactPointInput] | None = Field(
        None, description="Contact details of the location."
    )
    address: FhirAddressInput | None = Field(None, description="Physical location (0..1).")
    physicalType: FhirCodeableConceptInput | None = Field(
        None, description="Physical form of the location, e.g. building, room, vehicle, road."
    )
    position: LocationPositionInput | None = Field(
        None,
        description="The absolute geographic location (WGS84) — what the `near` search parameter measures from.",
    )
    managingOrganization: FhirReferenceInput | None = Field(
        None,
        description="Organization responsible for provisioning and upkeep — Reference(Organization). A relative 'Organization/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    partOf: FhirReferenceInput | None = Field(
        None,
        description="Another Location this one is physically a part of — Reference(Location). A relative 'Location/<id>' must exist in the caller's org, and may not make the hierarchy circular (422).",
    )
    hoursOfOperation: list[LocationHoursOfOperationInput] | None = Field(
        None, description="What days/times during a week is this location usually open."
    )
    availabilityExceptions: str | None = Field(
        None, description="Description of availability exceptions."
    )
    endpoint: list[FhirReferenceInput] | None = Field(
        None,
        description="Technical endpoints providing access to services operated for the location — Reference(Endpoint).",
    )


class LocationCreateSchema(_LocationFields):
    """POST body — a FHIR R4 Location resource, validated and stored whole."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class LocationPatchSchema(_LocationFields):
    """PATCH body — a partial FHIR R4 Location (merge-patch semantics on
    top-level elements). Only supplied elements are written; omitted ones
    are left untouched. A supplied element replaces the stored value
    wholesale — a list (even `[]`) replaces every entry, an object such as
    `address` or `partOf` replaces the whole element, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "suspended",
                "operationalStatus": {
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
                    "code": "K",
                    "display": "Contaminated",
                },
            }
        }
    }
