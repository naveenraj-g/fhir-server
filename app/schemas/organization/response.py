from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common.fhir import (
    FHIRAddress,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRHumanName,
    FHIRIdentifier,
    FHIRReference,
)

# Field descriptions below quote or closely paraphrase the official FHIR R4
# spec (https://www.hl7.org/fhir/R4/organization.html and
# https://www.hl7.org/fhir/R4/datatypes.html) for the corresponding element
# — see app/schemas/organization/input.py's module docstring for the same
# convention applied there.


# ── FHIR (camelCase) sub-schemas ──────────────────────────────────────────────


class FHIROrganizationContact(BaseModel):
    """Organization.contact — contact for the organization for a certain purpose."""

    purpose: FHIRCodeableConcept | None = Field(
        None, description="Indicates a purpose for which the contact can be reached."
    )
    name: FHIRHumanName | None = Field(
        None, description="A name associated with the contact."
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None,
        description="A contact detail (e.g. a telephone number or an email address) by which the party may be contacted.",
    )
    address: FHIRAddress | None = Field(
        None, description="Visiting or postal addresses for the contact."
    )


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


# ── Plain (snake_case) sub-schemas ────────────────────────────────────────────


class _AuditFields(BaseModel):
    """Shared audit trail fields present on every Organization sub-resource row
    — not part of FHIR itself, this codebase's own created/updated tracking."""

    model_config = ConfigDict(extra="allow")
    created_at: str | None = Field(None, description="When this row was created.")
    updated_at: str | None = Field(None, description="When this row was last updated.")
    created_by: str | None = Field(
        None, description="Acting user who created this row, forwarded by the gateway."
    )
    updated_by: str | None = Field(
        None,
        description="Acting user who last updated this row, forwarded by the gateway.",
    )


class PlainOrganizationIdentifier(_AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    use: str | None = Field(
        None, description="Identifies the purpose for this identifier, if known."
    )
    type_system: str | None = Field(
        None,
        description="The code system that defines the meaning of the identifier type code.",
    )
    type_version: str | None = Field(
        None,
        description="The version of the code system used for the identifier type code.",
    )
    type_code: str | None = Field(
        None,
        description="A symbol in syntax defined by the code system (e.g. NPI, DEA, license).",
    )
    type_display: str | None = Field(
        None, description="A representation of the meaning of the identifier type code."
    )
    type_text: str | None = Field(
        None, description="A human language representation of the identifier's type."
    )
    type_user_selected: bool | None = Field(
        None,
        description="Whether this identifier-type coding was chosen by a user directly.",
    )
    system: str | None = Field(
        None, description="Establishes the namespace for the value."
    )
    value: str | None = Field(
        None,
        description="The portion of the identifier typically relevant to the user, unique within the system.",
    )
    period_start: str | None = Field(
        None,
        description="Start of the time period during which this identifier is/was valid for use.",
    )
    period_end: str | None = Field(
        None,
        description="End of the time period during which this identifier is/was valid for use.",
    )
    assigner: str | None = Field(
        None,
        description="Resolved FHIR reference to the issuing organization, e.g. 'Organization/190001'.",
    )
    assigner_id: int | None = Field(
        None, description="Internal ID of the resolved assigning Organization, if any."
    )
    assigner_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the assigning organization.",
    )
    assigner_identifier_use: str | None = Field(
        None, description="Fallback identifier — its purpose, if known."
    )
    assigner_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — code system for its type."
    )
    assigner_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type code system."
    )
    assigner_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    assigner_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    assigner_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )
    assigner_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — whether its type was user-selected."
    )
    assigner_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    assigner_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    assigner_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    assigner_identifier_period_end: str | None = Field(
        None, description="Fallback identifier — end of validity period."
    )


class PlainOrganizationType(_AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    coding_system: str | None = Field(
        None,
        description="The code system that defines the meaning of the symbol in the code.",
    )
    coding_version: str | None = Field(
        None, description="The version of the code system used when choosing this code."
    )
    coding_code: str | None = Field(
        None, description="A symbol in syntax defined by the code system (e.g. 'prov')."
    )
    coding_display: str | None = Field(
        None, description="A representation of the meaning of the code in the system."
    )
    text: str | None = Field(
        None, description="A human language representation of the organization type."
    )
    coding_user_selected: bool | None = Field(
        None, description="Whether this coding was chosen by a user directly."
    )


class PlainOrganizationAlias(_AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    value: str | None = Field(
        None,
        description="An alternate name the organization is known as, or was known as in the past.",
    )


class PlainOrganizationTelecom(_AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    system: str | None = Field(
        None,
        description="Telecommunications form for the contact point (phone|fax|email|pager|url|sms|other).",
    )
    value: str | None = Field(
        None,
        description="The actual contact point details (e.g. a phone number or email address).",
    )
    use: str | None = Field(
        None, description="Identifies the purpose for the contact point."
    )
    rank: int | None = Field(
        None,
        description="Preferred order among a set of contacts — lower values are more preferred.",
    )
    period_start: str | None = Field(
        None,
        description="Start of the time period when this contact point was/is in use.",
    )
    period_end: str | None = Field(
        None,
        description="End of the time period when this contact point was/is in use.",
    )


class PlainOrganizationAddress(_AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    use: str | None = Field(None, description="The purpose of this address.")
    type: str | None = Field(
        None, description="Distinguishes between physical and mailing addresses."
    )
    text: str | None = Field(
        None,
        description="The entire address as it should be displayed, e.g. on a postal label.",
    )
    line: list[str] | None = Field(
        None,
        description="House number, apartment number, street name, and similar information.",
    )
    city: str | None = Field(
        None,
        description="The name of the city, town, suburb, village or other community.",
    )
    district: str | None = Field(
        None, description="The name of the administrative area (county)."
    )
    state: str | None = Field(
        None,
        description="Sub-unit of a country with limited sovereignty in a federally organized country.",
    )
    postal_code: str | None = Field(
        None,
        description="A postal code designating a region defined by the postal service.",
    )
    country: str | None = Field(
        None,
        description="Country — a nation as commonly understood or generally accepted.",
    )
    period_start: str | None = Field(
        None, description="Start of the time period when this address was/is in use."
    )
    period_end: str | None = Field(
        None, description="End of the time period when this address was/is in use."
    )


class PlainOrganizationContactTelecom(_AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    system: str | None = Field(
        None,
        description="Telecommunications form for the contact point (phone|fax|email|pager|url|sms|other).",
    )
    value: str | None = Field(None, description="The actual contact point details.")
    use: str | None = Field(
        None, description="Identifies the purpose for the contact point."
    )
    rank: int | None = Field(
        None,
        description="Preferred order among a set of contacts — lower values are more preferred.",
    )
    period_start: str | None = Field(
        None,
        description="Start of the time period when this contact point was/is in use.",
    )
    period_end: str | None = Field(
        None,
        description="End of the time period when this contact point was/is in use.",
    )


class PlainOrganizationContact(_AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    purpose_system: str | None = Field(
        None,
        description="The code system that defines the meaning of the contact's purpose code.",
    )
    purpose_code: str | None = Field(
        None,
        description="A symbol in syntax defined by the code system (e.g. 'ADMIN', 'BILL', 'PRESS').",
    )
    purpose_display: str | None = Field(
        None, description="A representation of the meaning of the purpose code."
    )
    purpose_text: str | None = Field(
        None, description="A human language representation of the contact's purpose."
    )
    name_use: str | None = Field(
        None, description="Identifies the purpose for this name."
    )
    name_text: str | None = Field(
        None, description="The entire name as it should be displayed."
    )
    name_family: str | None = Field(
        None, description="The part of the name that links to the genealogy."
    )
    name_given: list[str] | None = Field(None, description="Given name(s).")
    name_prefix: list[str] | None = Field(
        None,
        description="Name prefix(es) (e.g. titles) appearing at the start of the name.",
    )
    name_suffix: list[str] | None = Field(
        None, description="Name suffix(es) appearing at the end of the name."
    )
    name_period_start: str | None = Field(
        None,
        description="Start of the period during which this name was valid for the contact.",
    )
    name_period_end: str | None = Field(
        None,
        description="End of the period during which this name was valid for the contact.",
    )
    address_use: str | None = Field(None, description="The purpose of this address.")
    address_type: str | None = Field(
        None, description="Distinguishes between physical and mailing addresses."
    )
    address_text: str | None = Field(
        None, description="The entire address as it should be displayed."
    )
    address_line: list[str] | None = Field(
        None,
        description="House number, apartment number, street name, and similar information.",
    )
    address_city: str | None = Field(
        None,
        description="The name of the city, town, suburb, village or other community.",
    )
    address_district: str | None = Field(
        None, description="The name of the administrative area (county)."
    )
    address_state: str | None = Field(
        None,
        description="Sub-unit of a country with limited sovereignty in a federally organized country.",
    )
    address_postal_code: str | None = Field(
        None,
        description="A postal code designating a region defined by the postal service.",
    )
    address_country: str | None = Field(
        None,
        description="Country — a nation as commonly understood or generally accepted.",
    )
    address_period_start: str | None = Field(
        None, description="Start of the time period when this address was/is in use."
    )
    address_period_end: str | None = Field(
        None, description="End of the time period when this address was/is in use."
    )
    telecoms: list[PlainOrganizationContactTelecom] | None = Field(
        None,
        description="Contact detail(s) (e.g. a telephone number or an email address) by which the contact person may be reached.",
    )


class PlainOrganizationEndpoint(_AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    reference_type: str | None = Field(
        None, description="Resolved reference target type (always 'Endpoint')."
    )
    reference_id: int | None = Field(
        None,
        description="Internal ID of the resolved Endpoint, if any (Endpoint is not a modeled resource in this system).",
    )
    reference_display: str | None = Field(
        None, description="Plain text narrative that identifies the endpoint."
    )
    reference_identifier_use: str | None = Field(
        None, description="Fallback identifier — its purpose, if known."
    )
    reference_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — code system for its type."
    )
    reference_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type code system."
    )
    reference_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    reference_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    reference_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )
    reference_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — whether its type was user-selected."
    )
    reference_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    reference_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    reference_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    reference_identifier_period_end: str | None = Field(
        None, description="Fallback identifier — end of validity period."
    )


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
