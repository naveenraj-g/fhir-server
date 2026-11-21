from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirContactPointInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

from .backbone import (
    PractitionerRoleAvailableTimeInput,
    PractitionerRoleNotAvailableInput,
)

_EXAMPLE = {
    "resourceType": "PractitionerRole",
    "active": True,
    "period": {"start": "2026-01-01T00:00:00Z"},
    "practitioner": {"reference": "Practitioner/30001", "display": "Dr Adam Careful"},
    "organization": {"reference": "Organization/190001", "display": "General Hospital"},
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/role-id",
            "value": "R-1",
        }
    ],
    "code": [{"coding": [{"code": "doctor", "display": "Doctor"}]}],
    "specialty": [{"coding": [{"code": "394579002", "display": "Cardiology"}]}],
    "location": [{"reference": "Location/230001"}],
    "healthcareService": [{"reference": "HealthcareService/150001"}],
    "telecom": [{"system": "phone", "value": "555-0100", "use": "work"}],
    "availableTime": [
        {
            "daysOfWeek": ["mon", "tue"],
            "availableStartTime": "08:00:00",
            "availableEndTime": "17:00:00",
        }
    ],
    "notAvailable": [
        {"description": "Conference week", "during": {"start": "2026-09-01T00:00:00Z"}}
    ],
    "availabilityExceptions": "Not on public holidays",
    "endpoint": [{"reference": "Endpoint/620001"}],
}


class _PractitionerRoleFields(FhirInputModel):
    """Every writable PractitionerRole element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/practitionerrole.html). Create and patch
    accept exactly the same fields — PractitionerRole has no element that is
    required at this layer.

    The validated body is stored whole (PractitionerRoleModel.content), so any
    valid R4 element is kept — including ones this model doesn't declare.
    Server-managed elements are ignored if sent: `id` (assigned from the
    practitioner_role_id sequence) and `meta` (audit/tenant data, stamped on at
    read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["PractitionerRole"] | None = Field(
        None, description="Optional; if supplied it must be 'PractitionerRole'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Business Identifiers that are specific to a role/location."
    )
    active: bool | None = Field(
        None, description="Whether this practitioner role record is in active use."
    )
    period: FhirPeriodInput | None = Field(
        None,
        description="The period during which the practitioner is authorized to perform in these role(s).",
    )
    practitioner: FhirReferenceInput | None = Field(
        None,
        description="Practitioner that is able to provide the defined services for the organization — Reference(Practitioner). A relative 'Practitioner/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    organization: FhirReferenceInput | None = Field(
        None,
        description="Organization where the roles are available — Reference(Organization). A relative 'Organization/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    code: list[FhirCodeableConceptInput] | None = Field(
        None, description="Roles which this practitioner may perform."
    )
    specialty: list[FhirCodeableConceptInput] | None = Field(
        None, description="Specific specialty of the practitioner."
    )
    location: list[FhirReferenceInput] | None = Field(
        None,
        description="The location(s) at which this practitioner provides care — Reference(Location). A relative 'Location/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    healthcareService: list[FhirReferenceInput] | None = Field(
        None,
        description="The list of healthcare services that this worker provides for this role's Organization/Location(s) — Reference(HealthcareService). A relative 'HealthcareService/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    telecom: list[FhirContactPointInput] | None = Field(
        None,
        description="Contact details that are specific to the role/location/service.",
    )
    availableTime: list[PractitionerRoleAvailableTimeInput] | None = Field(
        None, description="Times the Service Site is available."
    )
    notAvailable: list[PractitionerRoleNotAvailableInput] | None = Field(
        None, description="Not available during this time due to provided reason."
    )
    availabilityExceptions: str | None = Field(
        None, description="Description of availability exceptions."
    )
    endpoint: list[FhirReferenceInput] | None = Field(
        None,
        description="Technical endpoints providing access to services operated for the practitioner with this role — Reference(Endpoint). A relative 'Endpoint/<id>' reference must exist in the caller's org (422 otherwise).",
    )


class PractitionerRoleCreateSchema(_PractitionerRoleFields):
    """POST body — a FHIR R4 PractitionerRole resource. Creates the role and
    every supplied nested element atomically in one transaction."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class PractitionerRolePatchSchema(_PractitionerRoleFields):
    """PATCH body — a partial FHIR R4 PractitionerRole (merge-patch semantics
    on top-level elements). Only supplied elements are written; omitted ones
    are left untouched. A supplied element replaces the stored value
    wholesale — a list (even `[]`) replaces every existing entry, an object
    such as `practitioner` or `period` replaces the whole value, and `null`
    clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "active": False,
                "period": {
                    "start": "2026-01-01T00:00:00Z",
                    "end": "2026-12-31T23:59:59Z",
                },
            }
        }
    }
