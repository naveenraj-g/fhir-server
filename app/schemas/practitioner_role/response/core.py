from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common.fhir import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRIdentifier,
    FHIRPeriod,
    FHIRReference,
)

from .available_time import (
    FHIRPractitionerRoleAvailableTime,
    PlainPractitionerRoleAvailableTime,
)
from .code import PlainPractitionerRoleCode
from .endpoint import PlainPractitionerRoleEndpoint
from .healthcare_service import PlainPractitionerRoleHealthcareService
from .identifier import PlainPractitionerRoleIdentifier
from .location import PlainPractitionerRoleLocation
from .not_available import (
    FHIRPractitionerRoleNotAvailable,
    PlainPractitionerRoleNotAvailable,
)
from .specialty import PlainPractitionerRoleSpecialty
from .telecom import PlainPractitionerRoleTelecom

# ── FHIR (camelCase) ────────────────────────────────────────────────────────


class FHIRPractitionerRoleSchema(BaseModel):
    resourceType: str = Field(
        "PractitionerRole", description="Always 'PractitionerRole'."
    )
    id: str = Field(..., description="Public practitioner_role_id as a string.")
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Business identifiers that are specific to a role/location."
    )
    active: bool | None = Field(
        None, description="Whether this practitioner role record is in active use."
    )
    period: FHIRPeriod | None = Field(
        None,
        description="The period during which the practitioner is authorized to perform in these role(s).",
    )
    practitioner: FHIRReference | None = Field(
        None, description="Practitioner providing services for the organization."
    )
    organization: FHIRReference | None = Field(
        None, description="Organization where the roles are available."
    )
    code: list[FHIRCodeableConcept] | None = Field(
        None, description="Roles which this practitioner may perform."
    )
    specialty: list[FHIRCodeableConcept] | None = Field(
        None, description="Specific expertise of the practitioner."
    )
    location: list[FHIRReference] | None = Field(
        None, description="The location(s) at which this practitioner provides care."
    )
    healthcareService: list[FHIRReference] | None = Field(
        None, description="Healthcare services provided at this role/location."
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None, description="Contact details that are specific to the role/location/service."
    )
    availableTime: list[FHIRPractitionerRoleAvailableTime] | None = Field(
        None, description="A collection of times the role is available."
    )
    notAvailable: list[FHIRPractitionerRoleNotAvailable] | None = Field(
        None,
        description="Not available during this period of time due to the provided reason.",
    )
    availabilityExceptions: str | None = Field(
        None, description="A description of site availability exceptions."
    )
    endpoint: list[FHIRReference] | None = Field(
        None,
        description="Technical endpoints providing access to services operated for this role.",
    )


class FHIRPractitionerRoleBundleEntry(BaseModel):
    resource: FHIRPractitionerRoleSchema


class FHIRPractitionerRoleBundle(FHIRBundle):
    entry: list[FHIRPractitionerRoleBundleEntry] | None = None


# ── Plain (snake_case) ───────────────────────────────────────────────────────


class PlainPractitionerRoleResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public practitioner_role_id.")
    active: bool | None = Field(
        None, description="Whether this practitioner role record is in active use."
    )
    period_start: str | None = Field(
        None,
        description="Start of the period during which the practitioner is authorized to perform in these role(s).",
    )
    period_end: str | None = Field(
        None,
        description="End of the period during which the practitioner is authorized to perform in these role(s).",
    )
    practitioner: str | None = Field(
        None,
        description="Resolved FHIR reference to the practitioner, e.g. 'Practitioner/30001'.",
    )
    practitioner_type: str | None = Field(
        None, description="Resolved reference target type (always 'Practitioner')."
    )
    practitioner_id: int | None = Field(
        None, description="Public practitioner_id of the resolved Practitioner, if any."
    )
    practitioner_display: str | None = Field(
        None, description="Plain text narrative that identifies the practitioner."
    )
    practitioner_identifier_use: str | None = Field(
        None, description="Fallback identifier — its purpose, if known."
    )
    practitioner_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — code system for its type."
    )
    practitioner_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type code system."
    )
    practitioner_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    practitioner_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    practitioner_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )
    practitioner_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — whether its type was user-selected."
    )
    practitioner_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    practitioner_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    practitioner_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    practitioner_identifier_period_end: str | None = Field(
        None, description="Fallback identifier — end of validity period."
    )
    organization: str | None = Field(
        None,
        description="Resolved FHIR reference to the organization, e.g. 'Organization/190001'.",
    )
    organization_type: str | None = Field(
        None, description="Resolved reference target type (always 'Organization')."
    )
    organization_id: int | None = Field(
        None, description="Public organization_id of the resolved Organization, if any."
    )
    organization_display: str | None = Field(
        None, description="Plain text narrative that identifies the organization."
    )
    organization_identifier_use: str | None = Field(
        None, description="Fallback identifier — its purpose, if known."
    )
    organization_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — code system for its type."
    )
    organization_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type code system."
    )
    organization_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    organization_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    organization_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )
    organization_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — whether its type was user-selected."
    )
    organization_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    organization_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    organization_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    organization_identifier_period_end: str | None = Field(
        None, description="Fallback identifier — end of validity period."
    )
    availability_exceptions: str | None = Field(
        None, description="A description of site availability exceptions."
    )
    identifier: list[PlainPractitionerRoleIdentifier] | None = Field(
        None, description="Business identifiers that are specific to a role/location."
    )
    code: list[PlainPractitionerRoleCode] | None = Field(
        None, description="Roles which this practitioner may perform."
    )
    specialty: list[PlainPractitionerRoleSpecialty] | None = Field(
        None, description="Specific expertise of the practitioner."
    )
    location: list[PlainPractitionerRoleLocation] | None = Field(
        None, description="Location(s) at which this practitioner provides care."
    )
    healthcare_service: list[PlainPractitionerRoleHealthcareService] | None = Field(
        None, description="Healthcare service(s) provided at this role/location."
    )
    telecom: list[PlainPractitionerRoleTelecom] | None = Field(
        None, description="Contact detail(s) specific to the role/location/service."
    )
    available_time: list[PlainPractitionerRoleAvailableTime] | None = Field(
        None, description="Available time window(s)."
    )
    not_available: list[PlainPractitionerRoleNotAvailable] | None = Field(
        None, description="Not-available period(s)."
    )
    endpoint: list[PlainPractitionerRoleEndpoint] | None = Field(
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


class PaginatedPractitionerRoleResponse(BaseModel):
    total: int | None = Field(
        None, description="Total matching rows (null when total_mode=none)."
    )
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Number of rows skipped before this page.")
    data: list[PlainPractitionerRoleResponse]
