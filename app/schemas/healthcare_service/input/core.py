from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirAttachmentInput,
    FhirCodeableConceptInput,
    FhirContactPointInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirReferenceInput,
)

from .backbone import (
    HealthcareServiceAvailableTimeInput,
    HealthcareServiceEligibilityInput,
    HealthcareServiceNotAvailableInput,
)

_EXAMPLE = {
    "resourceType": "HealthcareService",
    "active": True,
    "name": "Cardiology Clinic",
    "providedBy": {"reference": "Organization/190001", "display": "General Hospital"},
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/service-id",
            "value": "SVC-1",
        }
    ],
    "category": [{"coding": [{"code": "35", "display": "Specialist Medical"}]}],
    "type": [{"coding": [{"code": "124", "display": "General Practice"}]}],
    "specialty": [{"coding": [{"code": "394579002", "display": "Cardiology"}]}],
    "location": [{"reference": "Location/230001"}],
    "coverageArea": [{"reference": "Location/230002"}],
    "comment": "Heart-health clinic.",
    "telecom": [{"system": "phone", "value": "555-1234", "use": "work"}],
    "appointmentRequired": True,
    "availableTime": [
        {
            "daysOfWeek": ["mon", "tue", "wed"],
            "availableStartTime": "08:00:00",
            "availableEndTime": "17:00:00",
        }
    ],
    "notAvailable": [
        {
            "description": "Closed for the holidays",
            "during": {"start": "2026-12-24T00:00:00Z", "end": "2026-12-26T00:00:00Z"},
        }
    ],
    "endpoint": [
        {
            "identifier": {
                "system": "https://fhir-server.dev/fhir/identifier-system/endpoint",
                "value": "EP-1",
            }
        }
    ],
}


class _HealthcareServiceFields(FhirInputModel):
    """Every writable HealthcareService element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/healthcareservice.html). Create and patch
    accept exactly the same fields — HealthcareService has no element that is
    required at this layer.

    The validated body is stored whole (HealthcareServiceModel.content), so
    any valid R4 element is kept — including ones this model doesn't
    declare. Server-managed elements are ignored if sent: `id` (assigned from
    the healthcare_service_id sequence) and `meta` (audit/tenant data,
    stamped on at read time). org_id and created_by/updated_by come from the
    verified JWT (actor.org_id / actor.sub), never the body. Like
    Organization and Location there is no user_id."""

    resourceType: Literal["HealthcareService"] | None = Field(
        None, description="Optional; if supplied it must be 'HealthcareService'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="External identifiers for this item."
    )
    active: bool | None = Field(
        None, description="Whether this HealthcareService record is in active use."
    )
    providedBy: FhirReferenceInput | None = Field(
        None,
        description="Organization that provides this service — Reference(Organization). A relative 'Organization/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    category: list[FhirCodeableConceptInput] | None = Field(
        None, description="Broad category of service being performed or delivered."
    )
    type: list[FhirCodeableConceptInput] | None = Field(
        None, description="Type of service that may be delivered or performed."
    )
    specialty: list[FhirCodeableConceptInput] | None = Field(
        None, description="Specialties handled by the HealthcareService."
    )
    location: list[FhirReferenceInput] | None = Field(
        None,
        description="Location(s) where service may be provided — Reference(Location). A relative 'Location/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    name: str | None = Field(
        None,
        description="Description of service as presented to a consumer while searching.",
    )
    comment: str | None = Field(
        None,
        description="Additional description and/or any specific issues not covered elsewhere.",
    )
    extraDetails: str | None = Field(
        None,
        description="Extra details about the service that can't be placed in the other fields (markdown).",
    )
    photo: FhirAttachmentInput | None = Field(
        None, description="Facilitates quick identification of the service."
    )
    telecom: list[FhirContactPointInput] | None = Field(
        None, description="Contacts related to the healthcare service."
    )
    coverageArea: list[FhirReferenceInput] | None = Field(
        None,
        description="Location(s) service is intended for/available to — Reference(Location). A relative 'Location/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    serviceProvisionCode: list[FhirCodeableConceptInput] | None = Field(
        None, description="Conditions under which service is available/offered."
    )
    eligibility: list[HealthcareServiceEligibilityInput] | None = Field(
        None,
        description="Specific eligibility requirements required to use the service.",
    )
    program: list[FhirCodeableConceptInput] | None = Field(
        None, description="Programs that this service is applicable to."
    )
    characteristic: list[FhirCodeableConceptInput] | None = Field(
        None, description="Collection of characteristics (attributes)."
    )
    communication: list[FhirCodeableConceptInput] | None = Field(
        None, description="The language that this service is offered in."
    )
    referralMethod: list[FhirCodeableConceptInput] | None = Field(
        None, description="Ways that the service accepts referrals."
    )
    appointmentRequired: bool | None = Field(
        None, description="If an appointment is required for access to this service."
    )
    availableTime: list[HealthcareServiceAvailableTimeInput] | None = Field(
        None, description="Times the Service Site is available."
    )
    notAvailable: list[HealthcareServiceNotAvailableInput] | None = Field(
        None, description="Not available during this time due to provided reason."
    )
    availabilityExceptions: str | None = Field(
        None, description="Description of availability exceptions."
    )
    endpoint: list[FhirReferenceInput] | None = Field(
        None,
        description="Technical endpoints providing access to electronic services operated for the healthcare service — Reference(Endpoint).",
    )


class HealthcareServiceCreateSchema(_HealthcareServiceFields):
    """POST body — a FHIR R4 HealthcareService resource. Creates the service
    and every supplied nested element atomically in one transaction."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class HealthcareServicePatchSchema(_HealthcareServiceFields):
    """PATCH body — a partial FHIR R4 HealthcareService (merge-patch
    semantics on top-level elements). Only supplied elements are written;
    omitted ones are left untouched. A supplied element replaces the stored
    value wholesale — a list (even `[]`) replaces every existing entry, an
    object such as `providedBy` replaces the whole Reference, and `null`
    clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Cardiology & Vascular Clinic",
                "telecom": [{"system": "phone", "value": "555-9999", "use": "work"}],
            }
        }
    }
