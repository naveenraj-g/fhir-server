from pydantic import BaseModel, Field

from app.schemas.common.fhir import (
    FHIRAddress,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRHumanName,
    FHIRIdentifier,
    FHIRPeriod,
    FHIRReference,
)

# ── FHIR (camelCase) sub-schemas ──────────────────────────────────────────────


class FHIRAttachment(BaseModel):
    contentType: str | None = Field(None, description="MIME type (e.g. image/png).")
    language: str | None = Field(None, description="BCP-47 language code.")
    data: str | None = Field(None, description="Base64-encoded binary data.")
    url: str | None = Field(None, description="URL where data can be accessed.")
    size: int | None = Field(None, description="Bytes before base64 encoding.")
    hash: str | None = Field(None, description="Base64-encoded SHA-1 hash.")
    title: str | None = Field(None, description="Label or display title.")
    creation: str | None = Field(None, description="ISO 8601 dateTime when created.")


class FHIRQualification(BaseModel):
    identifier: list[FHIRIdentifier] | None = None
    code: FHIRCodeableConcept | None = Field(
        None, description="Coded qualification type."
    )
    status: FHIRCodeableConcept | None = Field(
        None,
        description="Status of the qualification (e.g. active, inactive, pending).",
    )
    period: FHIRPeriod | None = Field(
        None, description="Qualification validity period."
    )
    issuer: FHIRReference | None = Field(
        None, description="Issuing organization reference."
    )


class FHIRCommunication(BaseModel):
    language: FHIRCodeableConcept | None = Field(
        None, description="Language as CodeableConcept (BCP-47)."
    )


class FHIRPractitionerSchema(BaseModel):
    resourceType: str = Field("Practitioner", description="Always 'Practitioner'.")
    id: str = Field(..., description="Public practitioner_id as a string.")
    active: bool | None = Field(
        None, description="Whether this practitioner record is active."
    )
    gender: str | None = Field(None, description="male | female | other | unknown")
    birthDate: str | None = Field(None, description="ISO 8601 date string.")
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Business identifiers (NPI, license, DEA, etc.)."
    )
    name: list[FHIRHumanName] | None = Field(
        None, description="Name(s) associated with the practitioner."
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None, description="Contact details applying to all roles."
    )
    address: list[FHIRAddress] | None = Field(
        None, description="Address(es) of the practitioner."
    )
    photo: list[FHIRAttachment] | None = Field(
        None, description="Image(s) of the practitioner."
    )
    qualification: list[FHIRQualification] | None = Field(
        None, description="Certifications, licenses, or training."
    )
    communication: list[FHIRCommunication] | None = Field(
        None, description="Languages used in patient communication."
    )


class FHIRPractitionerBundleEntry(BaseModel):
    resource: FHIRPractitionerSchema


class FHIRPractitionerBundle(FHIRBundle):
    entry: list[FHIRPractitionerBundleEntry] | None = None


# ── Plain (snake_case) sub-schemas ────────────────────────────────────────────


class PlainPractitionerName(BaseModel):
    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    use: str | None = Field(
        None,
        description="usual | official | temp | nickname | anonymous | old | maiden",
    )
    text: str | None = Field(None, description="Full display name.")
    family: str | None = Field(None, description="Family (last) name.")
    given: list[str] | None = Field(None, description="Given (first/middle) names.")
    prefix: list[str] | None = Field(
        None, description="Name prefixes (Mr., Dr., etc.)."
    )
    suffix: list[str] | None = Field(None, description="Name suffixes (Jr., MD, etc.).")
    period_start: str | None = Field(None, description="ISO 8601 datetime string.")
    period_end: str | None = Field(None, description="ISO 8601 datetime string.")
    created_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was created."
    )
    updated_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was last updated."
    )
    created_by: str | None = Field(
        None, description="Acting-user value recorded as the creator of this row."
    )
    updated_by: str | None = Field(
        None, description="Acting-user value recorded as the last updater of this row."
    )


class PlainPractitionerIdentifier(BaseModel):
    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    use: str | None = Field(
        None, description="usual | official | temp | secondary | old"
    )
    type_system: str | None = Field(
        None, description="Coding system URI for identifier type."
    )
    type_version: str | None = Field(
        None, description="Version of the coding system for identifier type."
    )
    type_code: str | None = Field(
        None, description="Identifier type code (e.g. NPI, DEA)."
    )
    type_display: str | None = Field(
        None, description="Human-readable identifier type."
    )
    type_text: str | None = Field(
        None, description="Plain-text description of identifier type."
    )
    type_user_selected: bool | None = Field(
        None,
        description="Whether this identifier-type coding was chosen directly by the user.",
    )
    system: str | None = Field(
        None, description="Namespace URI for the identifier value."
    )
    value: str | None = Field(None, description="The identifier value.")
    period_start: str | None = Field(None, description="ISO 8601 datetime string.")
    period_end: str | None = Field(None, description="ISO 8601 datetime string.")
    assigner_type: str | None = Field(
        None, description="Reference type for the assigning organization."
    )
    assigner_id: int | None = Field(
        None, description="Public id of the assigning Organization."
    )
    assigner_display: str | None = Field(
        None, description="Display name of the issuing organization."
    )
    assigner_identifier_use: str | None = Field(
        None,
        description="Fallback identifier (used when the assigning organization isn't a resource in this system) — usual|official|temp|secondary|old.",
    )
    assigner_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    assigner_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    assigner_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    assigner_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    assigner_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    assigner_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    assigner_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    assigner_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    assigner_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it became valid."
    )
    assigner_identifier_period_end: str | None = Field(
        None,
        description="Fallback identifier — ISO 8601 datetime it stopped being valid.",
    )
    created_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was created."
    )
    updated_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was last updated."
    )
    created_by: str | None = Field(
        None, description="Acting-user value recorded as the creator of this row."
    )
    updated_by: str | None = Field(
        None, description="Acting-user value recorded as the last updater of this row."
    )


class PlainPractitionerTelecom(BaseModel):
    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    system: str | None = Field(
        None, description="phone | fax | email | pager | url | sms | other"
    )
    value: str | None = Field(
        None,
        description="The actual contact point details (e.g. a phone number or email address).",
    )
    use: str | None = Field(None, description="home | work | temp | old | mobile")
    rank: int | None = Field(
        None,
        description="Preferred order among a set of contacts — lower values are more preferred.",
    )
    period_start: str | None = Field(None, description="ISO 8601 datetime string.")
    period_end: str | None = Field(None, description="ISO 8601 datetime string.")
    created_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was created."
    )
    updated_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was last updated."
    )
    created_by: str | None = Field(
        None, description="Acting-user value recorded as the creator of this row."
    )
    updated_by: str | None = Field(
        None, description="Acting-user value recorded as the last updater of this row."
    )


class PlainPractitionerAddress(BaseModel):
    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    use: str | None = Field(None, description="home | work | temp | old | billing")
    type: str | None = Field(None, description="postal | physical | both")
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
    period_start: str | None = Field(None, description="ISO 8601 datetime string.")
    period_end: str | None = Field(None, description="ISO 8601 datetime string.")
    created_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was created."
    )
    updated_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was last updated."
    )
    created_by: str | None = Field(
        None, description="Acting-user value recorded as the creator of this row."
    )
    updated_by: str | None = Field(
        None, description="Acting-user value recorded as the last updater of this row."
    )


class PlainPractitionerPhoto(BaseModel):
    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    content_type: str | None = Field(
        None,
        description="MIME type of the content, with charset if applicable (e.g. image/png).",
    )
    language: str | None = Field(
        None,
        description="Human language of the content, as a BCP-47 code (e.g. en, fr).",
    )
    data: str | None = Field(None, description="The actual image data, base64-encoded.")
    url: str | None = Field(
        None,
        description="A URL where the image data can be retrieved instead of inline.",
    )
    size: int | None = Field(
        None,
        description="Number of bytes of content, measured after decoding from base64 if applicable.",
    )
    hash: str | None = Field(
        None,
        description="Base64-encoded hash (SHA-1) of the image data, used to verify integrity.",
    )
    title: str | None = Field(
        None, description="Label to display in place of the image content."
    )
    creation: str | None = Field(None, description="ISO 8601 datetime string.")
    created_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was created."
    )
    updated_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was last updated."
    )
    created_by: str | None = Field(
        None, description="Acting-user value recorded as the creator of this row."
    )
    updated_by: str | None = Field(
        None, description="Acting-user value recorded as the last updater of this row."
    )


class PlainQualificationIdentifier(BaseModel):
    id: int = Field(..., description="Internal row ID.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    use: str | None = Field(
        None, description="usual | official | temp | secondary | old"
    )
    type_system: str | None = Field(
        None, description="Coding system URI for identifier type."
    )
    type_version: str | None = Field(
        None, description="Version of the coding system for identifier type."
    )
    type_code: str | None = Field(None, description="Identifier type code.")
    type_display: str | None = Field(
        None, description="Human-readable identifier type."
    )
    type_text: str | None = Field(
        None, description="Plain-text description of identifier type."
    )
    type_user_selected: bool | None = Field(
        None,
        description="Whether this identifier-type coding was chosen directly by the user.",
    )
    system: str | None = Field(
        None, description="Namespace URI for the qualification identifier."
    )
    value: str | None = Field(None, description="Qualification or license number.")
    period_start: str | None = Field(None, description="ISO 8601 datetime string.")
    period_end: str | None = Field(None, description="ISO 8601 datetime string.")
    assigner_type: str | None = Field(
        None, description="Reference type for the assigning organization."
    )
    assigner_id: int | None = Field(
        None, description="Public id of the assigning Organization."
    )
    assigner_display: str | None = Field(
        None, description="Display name of the issuing organization."
    )
    assigner_identifier_use: str | None = Field(
        None,
        description="Fallback identifier (used when the assigning organization isn't a resource in this system) — usual|official|temp|secondary|old.",
    )
    assigner_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    assigner_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    assigner_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    assigner_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    assigner_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    assigner_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    assigner_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    assigner_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    assigner_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it became valid."
    )
    assigner_identifier_period_end: str | None = Field(
        None,
        description="Fallback identifier — ISO 8601 datetime it stopped being valid.",
    )
    created_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was created."
    )
    updated_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was last updated."
    )
    created_by: str | None = Field(
        None, description="Acting-user value recorded as the creator of this row."
    )
    updated_by: str | None = Field(
        None, description="Acting-user value recorded as the last updater of this row."
    )


class PlainQualification(BaseModel):
    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    identifier: list[PlainQualificationIdentifier] | None = Field(
        None, description="Identifiers for this qualification (e.g. license numbers)."
    )
    code_system: str | None = Field(
        None, description="Coding system URI for qualification type."
    )
    code_code: str | None = Field(None, description="Coded qualification type.")
    code_display: str | None = Field(
        None, description="Display for the qualification code."
    )
    code_text: str | None = Field(
        None, description="Human-readable qualification type."
    )
    status_system: str | None = Field(
        None, description="Coding system URI for qualification status."
    )
    status_code: str | None = Field(
        None, description="Status code (e.g. active, inactive, pending)."
    )
    status_display: str | None = Field(None, description="Display for the status code.")
    status_text: str | None = Field(
        None, description="Human-readable qualification status."
    )
    period_start: str | None = Field(None, description="ISO 8601 datetime string.")
    period_end: str | None = Field(
        None, description="ISO 8601 datetime string — qualification expiry."
    )
    issuer_type: str | None = Field(
        None, description="Reference type for issuer, always 'Organization'."
    )
    issuer_id: int | None = Field(
        None, description="Public Organization ID that issued the qualification."
    )
    issuer_display: str | None = Field(
        None, description="Display name of the issuing organization."
    )
    issuer_identifier_use: str | None = Field(
        None,
        description="Fallback identifier (used when the issuing organization isn't a resource in this system) — usual|official|temp|secondary|old.",
    )
    issuer_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    issuer_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    issuer_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    issuer_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    issuer_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    issuer_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    issuer_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    issuer_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    issuer_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it became valid."
    )
    issuer_identifier_period_end: str | None = Field(
        None,
        description="Fallback identifier — ISO 8601 datetime it stopped being valid.",
    )
    created_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was created."
    )
    updated_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was last updated."
    )
    created_by: str | None = Field(
        None, description="Acting-user value recorded as the creator of this row."
    )
    updated_by: str | None = Field(
        None, description="Acting-user value recorded as the last updater of this row."
    )


class PlainPractitionerCommunication(BaseModel):
    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    language_system: str | None = Field(
        None, description="URI of the language code system."
    )
    language_version: str | None = Field(
        None, description="Version of the language code system."
    )
    language_code: str | None = Field(
        None, description="ISO-639-1 language code (e.g. en, fr, de)."
    )
    language_display: str | None = Field(
        None,
        description="A representation of the meaning of the language code, following the rules of the system.",
    )
    language_text: str | None = Field(
        None,
        description="A human language representation of the language, as seen/selected/entered by the user.",
    )
    language_user_selected: bool | None = Field(
        None,
        description="Whether this language coding was chosen directly by the user.",
    )
    created_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was created."
    )
    updated_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was last updated."
    )
    created_by: str | None = Field(
        None, description="Acting-user value recorded as the creator of this row."
    )
    updated_by: str | None = Field(
        None, description="Acting-user value recorded as the last updater of this row."
    )


# ── Plain Practitioner response ───────────────────────────────────────────────


class PlainPractitionerResponse(BaseModel):
    id: int = Field(..., description="Public practitioner_id.")
    user_id: str | None = Field(
        None,
        description="Gateway-forwarded ID of the user who owns this record (JWT sub) — describes who this row belongs to, not a field of the FHIR Practitioner resource itself.",
    )
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    active: bool | None = Field(
        None, description="Whether this practitioner's record is in active use."
    )
    gender: str | None = Field(
        None,
        description="Administrative Gender — the gender that the person is considered to have for administration and record keeping purposes. male|female|other|unknown.",
    )
    birth_date: str | None = Field(
        None,
        description="The date of birth for the practitioner (ISO 8601 date string).",
    )
    name: list[PlainPractitionerName] | None = Field(
        None, description="The name(s) associated with the practitioner."
    )
    identifier: list[PlainPractitionerIdentifier] | None = Field(
        None, description="An identifier that applies to this person in this role."
    )
    telecom: list[PlainPractitionerTelecom] | None = Field(
        None,
        description="A contact detail for the practitioner (that apply to all roles).",
    )
    address: list[PlainPractitionerAddress] | None = Field(
        None,
        description="Address(es) of the practitioner that are not role specific (typically home address).",
    )
    photo: list[PlainPractitionerPhoto] | None = Field(
        None, description="Image of the person."
    )
    qualification: list[PlainQualification] | None = Field(
        None,
        description="Certification, license, or training pertaining to the provision of care.",
    )
    communication: list[PlainPractitionerCommunication] | None = Field(
        None,
        description="A language the practitioner can use in patient communication.",
    )
    created_at: str | None = Field(
        None, description="When this row was created (ISO 8601 datetime string)."
    )
    updated_at: str | None = Field(
        None, description="When this row was last updated (ISO 8601 datetime string)."
    )
    created_by: str | None = Field(
        None,
        description="Acting user who created this record, forwarded by the gateway.",
    )
    updated_by: str | None = Field(
        None,
        description="Acting user who last updated this record, forwarded by the gateway.",
    )


# ── Paginated response ────────────────────────────────────────────────────────


class PaginatedPractitionerResponse(BaseModel):
    total: int = Field(..., description="Total number of matching practitioners.")
    limit: int = Field(..., description="Page size requested.")
    offset: int = Field(..., description="Number of records skipped.")
    data: list[PlainPractitionerResponse] = Field(
        ..., description="Array of plain-JSON Practitioner objects."
    )


# ── Sub-resource list responses ───────────────────────────────────────────────


class PractitionerNamesListResponse(BaseModel):
    data: list[PlainPractitionerName]
    total: int = Field(..., description="Total count of name entries.")


class PractitionerIdentifiersListResponse(BaseModel):
    data: list[PlainPractitionerIdentifier]
    total: int = Field(..., description="Total count of identifier entries.")


class PractitionerTelecomListResponse(BaseModel):
    data: list[PlainPractitionerTelecom]
    total: int = Field(..., description="Total count of contact point entries.")


class PractitionerAddressesListResponse(BaseModel):
    data: list[PlainPractitionerAddress]
    total: int = Field(..., description="Total count of address entries.")


class PractitionerPhotosListResponse(BaseModel):
    data: list[PlainPractitionerPhoto]
    total: int = Field(..., description="Total count of photo entries.")


class PractitionerQualificationsListResponse(BaseModel):
    data: list[PlainQualification]
    total: int = Field(..., description="Total count of qualification entries.")


class PractitionerCommunicationsListResponse(BaseModel):
    data: list[PlainPractitionerCommunication]
    total: int = Field(..., description="Total count of communication entries.")


# ── FHIR sub-resource list responses ──────────────────────────────────────────


class FHIRPractitionerNameListItem(FHIRHumanName):
    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPractitionerNamesListResponse(BaseModel):
    data: list[FHIRPractitionerNameListItem]
    total: int = Field(..., description="Total count of name entries.")


class FHIRPractitionerIdentifierListItem(FHIRIdentifier):
    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPractitionerIdentifiersListResponse(BaseModel):
    data: list[FHIRPractitionerIdentifierListItem]
    total: int = Field(..., description="Total count of identifier entries.")


class FHIRPractitionerTelecomListItem(FHIRContactPoint):
    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPractitionerTelecomListResponse(BaseModel):
    data: list[FHIRPractitionerTelecomListItem]
    total: int = Field(..., description="Total count of contact point entries.")


class FHIRPractitionerAddressListItem(FHIRAddress):
    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPractitionerAddressesListResponse(BaseModel):
    data: list[FHIRPractitionerAddressListItem]
    total: int = Field(..., description="Total count of address entries.")


class FHIRPractitionerPhotoListItem(FHIRAttachment):
    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPractitionerPhotosListResponse(BaseModel):
    data: list[FHIRPractitionerPhotoListItem]
    total: int = Field(..., description="Total count of photo entries.")


class FHIRPractitionerQualificationListItem(FHIRQualification):
    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPractitionerQualificationsListResponse(BaseModel):
    data: list[FHIRPractitionerQualificationListItem]
    total: int = Field(..., description="Total count of qualification entries.")


class FHIRPractitionerCommunicationListItem(FHIRCommunication):
    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPractitionerCommunicationsListResponse(BaseModel):
    data: list[FHIRPractitionerCommunicationListItem]
    total: int = Field(..., description="Total count of communication entries.")
