from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common.fhir import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRIdentifier,
    FHIRReference,
)

from .available_time import (
    FHIRHealthcareServiceAvailableTime,
    PlainHealthcareServiceAvailableTime,
)
from .category import PlainHealthcareServiceCategory
from .characteristic import PlainHealthcareServiceCharacteristic
from .communication import PlainHealthcareServiceCommunication
from .coverage_area import PlainHealthcareServiceCoverageArea
from .eligibility import (
    FHIRHealthcareServiceEligibility,
    PlainHealthcareServiceEligibility,
)
from .endpoint import PlainHealthcareServiceEndpoint
from .identifier import PlainHealthcareServiceIdentifier
from .location import PlainHealthcareServiceLocation
from .not_available import (
    FHIRHealthcareServiceNotAvailable,
    PlainHealthcareServiceNotAvailable,
)
from .program import PlainHealthcareServiceProgram
from .referral_method import PlainHealthcareServiceReferralMethod
from .service_provision_code import PlainHealthcareServiceServiceProvisionCode
from .specialty import PlainHealthcareServiceSpecialty
from .telecom import PlainHealthcareServiceTelecom
from .type import PlainHealthcareServiceType

# ── FHIR (camelCase) ────────────────────────────────────────────────────────


class FHIRAttachment(BaseModel):
    """FHIR R4 Attachment — HealthcareService.photo."""

    contentType: str | None = Field(
        None, description="Mime type of the content (e.g. image/png)."
    )
    language: str | None = Field(
        None, description="Human language of the content, as a BCP-47 code."
    )
    data: str | None = Field(None, description="The actual data, base64-encoded.")
    url: str | None = Field(
        None, description="A URI where the data can be found instead of inline."
    )
    size: int | None = Field(
        None,
        description="Number of bytes of content, measured after decoding, if applicable.",
    )
    hash: str | None = Field(
        None, description="Base64-encoded hash (SHA-1) of the data."
    )
    title: str | None = Field(
        None, description="Label to display in place of the content."
    )
    creation: str | None = Field(
        None, description="ISO 8601 datetime the attachment was first created."
    )


class FHIRHealthcareServiceSchema(BaseModel):
    resourceType: str = Field(
        "HealthcareService", description="Always 'HealthcareService'."
    )
    id: str = Field(..., description="Public healthcare_service_id as a string.")
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External identifiers for this item."
    )
    active: bool | None = Field(
        None, description="Whether this healthcare service record is in active use."
    )
    providedBy: FHIRReference | None = Field(
        None, description="The organization that provides this healthcare service."
    )
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="Broad category of service being performed or delivered."
    )
    type: list[FHIRCodeableConcept] | None = Field(
        None, description="Specific type of service that may be delivered or performed."
    )
    specialty: list[FHIRCodeableConcept] | None = Field(
        None, description="Collection of specialties handled by the service site."
    )
    location: list[FHIRReference] | None = Field(
        None,
        description="The location(s) where this healthcare service may be provided.",
    )
    name: str | None = Field(
        None,
        description="Further description of the service as presented to a consumer while searching.",
    )
    comment: str | None = Field(
        None, description="Any additional description of the service."
    )
    extraDetails: str | None = Field(
        None, description="Extra details about the service (markdown)."
    )
    photo: FHIRAttachment | None = Field(
        None, description="Facilitates quick identification of the service."
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None, description="Contact details for the healthcare service."
    )
    coverageArea: list[FHIRReference] | None = Field(
        None, description="Location(s) this service is available to."
    )
    serviceProvisionCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Conditions under which the service is available/offered."
    )
    eligibility: list[FHIRHealthcareServiceEligibility] | None = Field(
        None, description="Specific eligibility requirements for using the service."
    )
    program: list[FHIRCodeableConcept] | None = Field(
        None, description="Programs that this service is applicable to."
    )
    characteristic: list[FHIRCodeableConcept] | None = Field(
        None, description="Collection of characteristics (attributes)."
    )
    communication: list[FHIRCodeableConcept] | None = Field(
        None,
        description="Languages that people who work at/perform the service can use.",
    )
    referralMethod: list[FHIRCodeableConcept] | None = Field(
        None, description="Ways that the service accepts referrals."
    )
    appointmentRequired: bool | None = Field(
        None,
        description="Whether or not a prospective consumer will require an appointment.",
    )
    availableTime: list[FHIRHealthcareServiceAvailableTime] | None = Field(
        None, description="Collection of times the healthcare service is available."
    )
    notAvailable: list[FHIRHealthcareServiceNotAvailable] | None = Field(
        None,
        description="Not available during this period of time due to the provided reason.",
    )
    availabilityExceptions: str | None = Field(
        None, description="A description of site availability exceptions."
    )
    endpoint: list[FHIRReference] | None = Field(
        None,
        description="Technical endpoints providing access to services operated for this healthcare service.",
    )


class FHIRHealthcareServiceBundleEntry(BaseModel):
    resource: FHIRHealthcareServiceSchema


class FHIRHealthcareServiceBundle(FHIRBundle):
    entry: list[FHIRHealthcareServiceBundleEntry] | None = None


# ── Plain (snake_case) ───────────────────────────────────────────────────────


class PlainHealthcareServiceResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public healthcare_service_id.")
    active: bool | None = Field(
        None, description="Whether this healthcare service record is in active use."
    )
    name: str | None = Field(
        None,
        description="Further description of the service as presented to a consumer while searching.",
    )
    provided_by: str | None = Field(
        None,
        description="Resolved FHIR reference to the providing organization, e.g. 'Organization/190001'.",
    )
    provided_by_type: str | None = Field(
        None, description="Resolved reference target type (always 'Organization')."
    )
    provided_by_id: int | None = Field(
        None, description="Public organization_id of the resolved Organization, if any."
    )
    provided_by_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the providing organization.",
    )
    provided_by_identifier_use: str | None = Field(
        None, description="Fallback identifier — its purpose, if known."
    )
    provided_by_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — code system for its type."
    )
    provided_by_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type code system."
    )
    provided_by_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    provided_by_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    provided_by_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )
    provided_by_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — whether its type was user-selected."
    )
    provided_by_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    provided_by_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    provided_by_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    provided_by_identifier_period_end: str | None = Field(
        None, description="Fallback identifier — end of validity period."
    )
    comment: str | None = Field(
        None, description="Any additional description of the service."
    )
    extra_details: str | None = Field(
        None, description="Extra details about the service (markdown)."
    )
    photo_content_type: str | None = Field(
        None, description="MIME type of the photo (e.g. image/png)."
    )
    photo_language: str | None = Field(
        None, description="Human language of the photo content."
    )
    photo_data: str | None = Field(
        None, description="The actual photo data, base64-encoded."
    )
    photo_url: str | None = Field(
        None, description="A URL where the photo can be retrieved instead of inline."
    )
    photo_size: int | None = Field(
        None,
        description="Number of bytes of content, measured after decoding, if applicable.",
    )
    photo_hash: str | None = Field(
        None, description="Base64-encoded hash (SHA-1) of the photo data."
    )
    photo_title: str | None = Field(
        None, description="Label to display in place of the photo content."
    )
    photo_creation: str | None = Field(
        None, description="ISO 8601 datetime the photo was first created."
    )
    appointment_required: bool | None = Field(
        None, description="Whether a prospective consumer will require an appointment."
    )
    availability_exceptions: str | None = Field(
        None, description="A description of site availability exceptions."
    )
    identifier: list[PlainHealthcareServiceIdentifier] | None = Field(
        None, description="External identifiers for this item."
    )
    category: list[PlainHealthcareServiceCategory] | None = Field(
        None, description="Broad category of service."
    )
    type: list[PlainHealthcareServiceType] | None = Field(
        None, description="Specific type(s) of service."
    )
    specialty: list[PlainHealthcareServiceSpecialty] | None = Field(
        None, description="Specialties handled by the service site."
    )
    location: list[PlainHealthcareServiceLocation] | None = Field(
        None, description="Location(s) where this service may be provided."
    )
    telecom: list[PlainHealthcareServiceTelecom] | None = Field(
        None, description="Contact details for the healthcare service."
    )
    coverage_area: list[PlainHealthcareServiceCoverageArea] | None = Field(
        None, description="Location(s) this service is available to."
    )
    service_provision_code: list[PlainHealthcareServiceServiceProvisionCode] | None = (
        Field(None, description="Conditions under which the service is available.")
    )
    eligibility: list[PlainHealthcareServiceEligibility] | None = Field(
        None, description="Specific eligibility requirements."
    )
    program: list[PlainHealthcareServiceProgram] | None = Field(
        None, description="Applicable program(s)."
    )
    characteristic: list[PlainHealthcareServiceCharacteristic] | None = Field(
        None, description="Characteristic(s) of the service."
    )
    communication: list[PlainHealthcareServiceCommunication] | None = Field(
        None, description="Communication language(s)."
    )
    referral_method: list[PlainHealthcareServiceReferralMethod] | None = Field(
        None, description="Referral method(s)."
    )
    available_time: list[PlainHealthcareServiceAvailableTime] | None = Field(
        None, description="Available time window(s)."
    )
    not_available: list[PlainHealthcareServiceNotAvailable] | None = Field(
        None, description="Not-available period(s)."
    )
    endpoint: list[PlainHealthcareServiceEndpoint] | None = Field(
        None, description="Technical endpoint(s)."
    )
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded ID of the tenant/account this record is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    created_at: str | None = Field(None, description="When this row was created.")
    updated_at: str | None = Field(None, description="When this row was last updated.")
    created_by: str | None = Field(
        None,
        description="Acting user who created this record, forwarded by the gateway.",
    )
    updated_by: str | None = Field(
        None,
        description="Acting user who last updated this record, forwarded by the gateway.",
    )


class PaginatedHealthcareServiceResponse(BaseModel):
    total: int | None = Field(
        None, description="Total matching rows (null when total_mode=none)."
    )
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Number of rows skipped before this page.")
    data: list[PlainHealthcareServiceResponse]
