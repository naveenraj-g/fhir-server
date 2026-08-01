from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common.fhir import (
    FHIRAddress,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRIdentifier,
    FHIRReference,
)

from .address import PlainOrganizationAddress
from .alias import PlainOrganizationAlias
from .contact import FHIROrganizationContact, PlainOrganizationContact
from .endpoint import PlainOrganizationEndpoint
from .identifier import PlainOrganizationIdentifier
from .telecom import PlainOrganizationTelecom
from .type import PlainOrganizationType

# ── FHIR (camelCase) ───────────────────────────────────────────────────────────


class FHIROrganizationSchema(BaseModel):
    resourceType: str = Field("Organization", description="Always 'Organization'.")
    id: str = Field(..., description="Public organization_id as a string.")
    active: bool | None = Field(
        None, description="Whether the organization's record is still in active use."
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None,
        description="Identifier(s) for the organization that is used to identify the organization across multiple disparate systems.",
    )
    type: list[FHIRCodeableConcept] | None = Field(
        None, description="The kind(s) of organization that this is."
    )
    name: str | None = Field(
        None, description="A name associated with the organization."
    )
    alias: list[str] | None = Field(
        None,
        description="A list of alternate names that the organization is known as, or was known as in the past.",
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None, description="A contact detail for the organization."
    )
    address: list[FHIRAddress] | None = Field(
        None, description="An address for the organization."
    )
    partOf: FHIRReference | None = Field(
        None, description="The organization of which this organization forms a part."
    )
    contact: list[FHIROrganizationContact] | None = Field(
        None, description="Contact for the organization for a certain purpose."
    )
    endpoint: list[FHIRReference] | None = Field(
        None,
        description="Technical endpoints providing access to services operated for the organization.",
    )


class FHIROrganizationBundleEntry(BaseModel):
    resource: FHIROrganizationSchema


class FHIROrganizationBundle(FHIRBundle):
    entry: list[FHIROrganizationBundleEntry] | None = None


# ── Plain (snake_case) ─────────────────────────────────────────────────────────


class PlainOrganizationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public organization_id.")
    active: bool | None = Field(
        None, description="Whether the organization's record is still in active use."
    )
    name: str | None = Field(
        None, description="A name associated with the organization."
    )
    partof: str | None = Field(
        None,
        description="Resolved FHIR reference to the parent organization, e.g. 'Organization/190001'.",
    )
    partof_type: str | None = Field(
        None, description="Resolved reference target type (always 'Organization')."
    )
    partof_id: int | None = Field(
        None, description="Internal ID of the resolved parent Organization, if any."
    )
    partof_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the parent organization.",
    )
    partof_identifier_use: str | None = Field(
        None, description="Fallback identifier — its purpose, if known."
    )
    partof_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — code system for its type."
    )
    partof_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type code system."
    )
    partof_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    partof_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    partof_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )
    partof_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — whether its type was user-selected."
    )
    partof_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    partof_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    partof_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    partof_identifier_period_end: str | None = Field(
        None, description="Fallback identifier — end of validity period."
    )
    identifier: list[PlainOrganizationIdentifier] | None = Field(
        None,
        description="Identifier(s) for the organization that is used to identify the organization across multiple disparate systems.",
    )
    type: list[PlainOrganizationType] | None = Field(
        None, description="The kind(s) of organization that this is."
    )
    alias: list[PlainOrganizationAlias] | None = Field(
        None,
        description="A list of alternate names that the organization is known as, or was known as in the past.",
    )
    telecom: list[PlainOrganizationTelecom] | None = Field(
        None, description="A contact detail for the organization."
    )
    address: list[PlainOrganizationAddress] | None = Field(
        None, description="An address for the organization."
    )
    contact: list[PlainOrganizationContact] | None = Field(
        None, description="Contact for the organization for a certain purpose."
    )
    endpoint: list[PlainOrganizationEndpoint] | None = Field(
        None,
        description="Technical endpoints providing access to services operated for the organization.",
    )
    user_id: str | None = Field(
        None,
        description="Gateway-forwarded ID of the user who owns this record — not a field of the Organization resource itself.",
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


class PaginatedOrganizationResponse(BaseModel):
    total: int | None = Field(
        None, description="Total matching rows (null when total_mode=none)."
    )
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Number of rows skipped before this page.")
    data: list[PlainOrganizationResponse]
