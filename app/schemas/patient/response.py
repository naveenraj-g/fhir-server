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

# ── FHIR contact BackboneElement sub-schemas ───────────────────────────────────


class FHIRPatientContact(BaseModel):
    """FHIR R4 Patient.contact BackboneElement — a contact party (guardian,
    partner, friend, etc.) for the patient."""

    relationship: list[FHIRCodeableConcept] | None = Field(
        None, description="The kind(s) of relationship this contact has to the patient."
    )
    name: FHIRHumanName | None = Field(
        None, description="A name associated with the contact person."
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None,
        description="Contact detail(s) (phone, email, etc.) for the contact person.",
    )
    address: FHIRAddress | None = Field(
        None, description="Address for the contact person."
    )
    gender: str | None = Field(None, description="male|female|other|unknown")
    organization: FHIRReference | None = Field(
        None,
        description=(
            "Organization on behalf of which the contact is acting or for which the "
            "contact is associated. Per pat-1, required if none of name, telecom, "
            "or address is given."
        ),
    )
    period: FHIRPeriod | None = Field(
        None,
        description="The period during which this contact is valid to be contacted regarding the patient.",
    )


# ── FHIR communication BackboneElement sub-schema ─────────────────────────────


class FHIRPatientCommunication(BaseModel):
    """FHIR R4 Patient.communication BackboneElement — a language the patient can
    use for healthcare-related communication."""

    language: FHIRCodeableConcept = Field(
        ...,
        description="The language which can be used to communicate with the patient about their health.",
    )
    preferred: bool | None = Field(
        None,
        description="Indicates whether this language is preferred for communicating with the patient.",
    )


# ── FHIR link BackboneElement sub-schema ──────────────────────────────────────


class FHIRPatientLink(BaseModel):
    """FHIR R4 Patient.link — a link to another Patient or RelatedPerson resource
    that concerns the same actual person."""

    other: FHIRReference = Field(
        ...,
        description="The other patient or related person resource that this link refers to.",
    )
    type: str = Field(..., description="replaced-by|replaces|refer|seealso")


# ── FHIR Attachment (photo) ────────────────────────────────────────────────────


class FHIRAttachment(BaseModel):
    """FHIR R4 Attachment — an image of the patient."""

    contentType: str | None = Field(
        None,
        description="Mime type of the content, with charset etc. (e.g. image/png).",
    )
    language: str | None = Field(
        None,
        description="Human language of the content, as a BCP-47 code (e.g. en, fr).",
    )
    data: str | None = Field(None, description="The actual image data, base64-encoded.")
    url: str | None = Field(
        None, description="A URI where the image data can be found instead of inline."
    )
    size: int | None = Field(
        None,
        description="Number of bytes of content, measured after decoding, if applicable.",
    )
    hash: str | None = Field(
        None,
        description="Base64-encoded hash (SHA-1) of the image data, used to verify integrity.",
    )
    title: str | None = Field(
        None, description="Label to display in place of the image content."
    )
    creation: str | None = Field(
        None, description="ISO 8601 datetime the image attachment was first created."
    )


# ── FHIR (camelCase) Patient schema ───────────────────────────────────────────


class FHIRPatientSchema(BaseModel):
    """FHIR R4 Patient resource — full representation including all sub-resource arrays."""

    resourceType: str = Field("Patient", description="Always 'Patient'.")
    id: str = Field(..., description="Public patient_id as a string.")
    active: bool | None = Field(
        None, description="Whether this patient's record is in active use."
    )
    gender: str | None = Field(None, description="male|female|other|unknown")
    birthDate: str | None = Field(
        None, description="ISO 8601 date (YYYY-MM-DD) of birth for the individual."
    )
    deceasedBoolean: bool | None = Field(
        None,
        description="deceased[x] choice — indicates the individual is deceased (boolean form).",
    )
    deceasedDateTime: str | None = Field(
        None,
        description="deceased[x] choice — ISO 8601 datetime the individual died (dateTime form).",
    )
    maritalStatus: FHIRCodeableConcept | None = Field(
        None, description="Marital (civil) status of the patient."
    )
    multipleBirthBoolean: bool | None = Field(
        None,
        description="multipleBirth[x] choice — whether the patient is part of a multiple birth (boolean form).",
    )
    multipleBirthInteger: int | None = Field(
        None,
        description="multipleBirth[x] choice — the patient's birth order in a multiple birth (integer form).",
    )
    name: list[FHIRHumanName] | None = Field(
        None, description="Name(s) associated with the patient."
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None,
        description="Business identifier(s) for this patient (e.g. MRN, SSN, passport).",
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None, description="Contact detail(s) (phone, email, etc.) for the patient."
    )
    address: list[FHIRAddress] | None = Field(
        None, description="Address(es) for the patient."
    )
    photo: list[FHIRAttachment] | None = Field(
        None, description="Image(s) of the patient."
    )
    contact: list[FHIRPatientContact] | None = Field(
        None,
        description="Contact party(-ies) (guardian, partner, friend) for the patient.",
    )
    communication: list[FHIRPatientCommunication] | None = Field(
        None,
        description="Language(s) the patient can use for healthcare-related communication.",
    )
    generalPractitioner: list[FHIRReference] | None = Field(
        None, description="Patient's nominated primary care provider(s)."
    )
    managingOrganization: FHIRReference | None = Field(
        None, description="Organization that is the custodian of the patient record."
    )
    link: list[FHIRPatientLink] | None = Field(
        None,
        description="Link(s) to other Patient/RelatedPerson resources concerning the same actual person.",
    )


class FHIRPatientCoreSchema(BaseModel):
    """
    FHIR R4 Patient resource shape for GET /{patient_id}/core — scalar fields
    only. Unlike FHIRPatientSchema, this model declares no sub-resource array
    fields (name, identifier, telecom, address, photo, contact, communication,
    generalPractitioner) at all, since that endpoint's mapper
    (to_fhir_patient_core()) never returns them.
    """

    resourceType: str = Field("Patient", description="Always 'Patient'.")
    id: str = Field(..., description="Public patient_id as a string.")
    active: bool | None = Field(
        None, description="Whether this patient's record is in active use."
    )
    gender: str | None = Field(None, description="male|female|other|unknown")
    birthDate: str | None = Field(
        None, description="ISO 8601 date (YYYY-MM-DD) of birth for the individual."
    )
    deceasedBoolean: bool | None = Field(
        None,
        description="deceased[x] choice — indicates the individual is deceased (boolean form).",
    )
    deceasedDateTime: str | None = Field(
        None,
        description="deceased[x] choice — ISO 8601 datetime the individual died (dateTime form).",
    )
    maritalStatus: FHIRCodeableConcept | None = Field(
        None, description="Marital (civil) status of the patient."
    )
    multipleBirthBoolean: bool | None = Field(
        None,
        description="multipleBirth[x] choice — whether the patient is part of a multiple birth (boolean form).",
    )
    multipleBirthInteger: int | None = Field(
        None,
        description="multipleBirth[x] choice — the patient's birth order in a multiple birth (integer form).",
    )
    managingOrganization: FHIRReference | None = Field(
        None, description="Organization that is the custodian of the patient record."
    )


class FHIRPatientBundleEntry(BaseModel):
    """FHIR R4 Bundle.entry wrapping a single Patient resource."""

    resource: FHIRPatientSchema = Field(
        ..., description="A single Patient resource within the search-set bundle."
    )


class FHIRPatientBundle(FHIRBundle):
    """FHIR R4 Bundle of type 'searchset' wrapping paginated Patient results."""

    entry: list[FHIRPatientBundleEntry] | None = Field(
        None, description="Patient resources matching the search, one per entry."
    )


# ── Plain (snake_case) sub-types ───────────────────────────────────────────────


class PlainPatientName(BaseModel):
    """Plain-JSON HumanName — a name associated with the patient."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(None, description="Tenant/ownership organization id.")
    use: str | None = Field(
        None, description="usual|official|temp|nickname|anonymous|old|maiden"
    )
    text: str | None = Field(None, description="Full name as a display string.")
    family: str | None = Field(None, description="Family (last) name.")
    given: list[str] | None = Field(
        None, description="Given (first/middle) names, in order."
    )
    prefix: list[str] | None = Field(
        None, description="Name prefixes (Mr., Dr., etc.)."
    )
    suffix: list[str] | None = Field(None, description="Name suffixes (Jr., MD, etc.).")
    period_start: str | None = Field(
        None, description="ISO 8601 datetime this name became valid."
    )
    period_end: str | None = Field(
        None, description="ISO 8601 datetime this name stopped being valid."
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


class PlainPatientIdentifier(BaseModel):
    """Plain-JSON Identifier — a business identifier for this patient."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(None, description="Tenant/ownership organization id.")
    use: str | None = Field(None, description="usual|official|temp|secondary|old")
    type_system: str | None = Field(
        None, description="Coding system for identifier type."
    )
    type_version: str | None = Field(
        None, description="Version of the coding system for identifier type."
    )
    type_code: str | None = Field(
        None, description="Code for identifier type (e.g. MR, SS)."
    )
    type_display: str | None = Field(None, description="Display for identifier type.")
    type_text: str | None = Field(
        None, description="Text of the CodeableConcept for identifier type."
    )
    type_user_selected: bool | None = Field(
        None, description="Whether this coding was chosen directly by the user."
    )
    system: str | None = Field(None, description="URI namespace of the identifier.")
    value: str | None = Field(
        None, description="Identifier value within the given system."
    )
    period_start: str | None = Field(
        None, description="ISO 8601 datetime this identifier became valid."
    )
    period_end: str | None = Field(
        None, description="ISO 8601 datetime this identifier stopped being valid."
    )
    assigner_type: str | None = Field(
        None, description="Reference type for the assigning organization."
    )
    assigner_id: int | None = Field(
        None, description="Public id of the assigning Organization."
    )
    assigner_display: str | None = Field(
        None, description="Display text for the assigning organization."
    )
    assigner_identifier_use: str | None = Field(
        None,
        description="Fallback identifier (used when the assigning organization "
        "isn't a resource in this system) — usual|official|temp|secondary|old.",
    )
    assigner_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    assigner_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    assigner_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type (e.g. MR, SS)."
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
        None, description="Fallback identifier — ISO 8601 datetime it stopped being valid."
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


class PlainPatientTelecom(BaseModel):
    """Plain-JSON ContactPoint — a contact detail for the patient."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(None, description="Tenant/ownership organization id.")
    system: str | None = Field(None, description="phone|fax|email|pager|url|sms|other")
    value: str | None = Field(
        None, description="Contact point details (phone number, email address, etc.)."
    )
    use: str | None = Field(None, description="home|work|temp|old|mobile")
    rank: int | None = Field(
        None, description="Preferred order of use — 1 indicates the most preferred."
    )
    period_start: str | None = Field(
        None, description="ISO 8601 datetime this contact point became valid."
    )
    period_end: str | None = Field(
        None, description="ISO 8601 datetime this contact point stopped being valid."
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


class PlainPatientAddress(BaseModel):
    """Plain-JSON Address — a postal or physical address for the patient."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(None, description="Tenant/ownership organization id.")
    use: str | None = Field(None, description="home|work|temp|old|billing")
    type: str | None = Field(None, description="postal|physical|both")
    text: str | None = Field(None, description="Full address as a display string.")
    line: list[str] | None = Field(None, description="Street address lines, in order.")
    city: str | None = Field(None, description="Name of city, town, or community.")
    district: str | None = Field(None, description="County or administrative district.")
    state: str | None = Field(
        None, description="Sub-unit of country — state, province, etc."
    )
    postal_code: str | None = Field(None, description="Postal/ZIP code for the area.")
    country: str | None = Field(
        None, description="Country — e.g. an ISO 3166 2- or 3-letter code."
    )
    period_start: str | None = Field(
        None, description="ISO 8601 datetime this address became valid."
    )
    period_end: str | None = Field(
        None, description="ISO 8601 datetime this address stopped being valid."
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


class PlainPatientPhoto(BaseModel):
    """Plain-JSON Attachment — an image of the patient."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(None, description="Tenant/ownership organization id.")
    content_type: str | None = Field(None, description="MIME type (e.g. image/png).")
    language: str | None = Field(None, description="BCP-47 language code.")
    data: str | None = Field(None, description="Base64-encoded image data.")
    url: str | None = Field(None, description="URL where the image can be retrieved.")
    size: int | None = Field(None, description="Size in bytes, after base64 decoding.")
    hash: str | None = Field(
        None, description="Base64-encoded SHA-1 hash of the image data."
    )
    title: str | None = Field(None, description="Label or display title.")
    creation: str | None = Field(
        None, description="ISO 8601 datetime the image was created."
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


class PlainContactRelationship(BaseModel):
    """Plain-JSON CodeableConcept — the kind of relationship a Patient.contact has to the patient."""

    id: int = Field(..., description="Internal row ID.")
    org_id: str | None = Field(None, description="Tenant/ownership organization id.")
    coding_system: str | None = Field(
        None, description="Coding system that defines this relationship code."
    )
    coding_version: str | None = Field(
        None, description="Version of the coding system."
    )
    coding_code: str | None = Field(
        None,
        description="Code for the nature of the relationship (e.g. C, N, MTH, FTH).",
    )
    coding_display: str | None = Field(
        None, description="Human-readable display for the relationship code."
    )
    text: str | None = Field(
        None, description="Plain-text rendering of the relationship CodeableConcept."
    )
    coding_user_selected: bool | None = Field(
        None, description="Whether this coding was chosen directly by the user."
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


class PlainContactTelecom(BaseModel):
    """Plain-JSON ContactPoint — a contact detail for the patient's contact person."""

    id: int = Field(..., description="Internal row ID.")
    org_id: str | None = Field(None, description="Tenant/ownership organization id.")
    system: str | None = Field(None, description="phone|fax|email|pager|url|sms|other")
    value: str | None = Field(
        None, description="Contact point details (phone number, email address, etc.)."
    )
    use: str | None = Field(None, description="home|work|temp|old|mobile")
    rank: int | None = Field(
        None, description="Preferred order of use — 1 indicates the most preferred."
    )
    period_start: str | None = Field(
        None, description="ISO 8601 datetime this contact point became valid."
    )
    period_end: str | None = Field(
        None, description="ISO 8601 datetime this contact point stopped being valid."
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


class PlainPatientContact(BaseModel):
    """Plain-JSON Patient.contact BackboneElement — a contact party (guardian,
    next-of-kin, emergency contact) for the patient."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(None, description="Tenant/ownership organization id.")
    relationship: list[PlainContactRelationship] | None = Field(
        None, description="The kind(s) of relationship this contact has to the patient."
    )
    name_use: str | None = Field(
        None, description="usual|official|temp|nickname|anonymous|old|maiden"
    )
    name_text: str | None = Field(
        None, description="Full name of the contact person as a display string."
    )
    name_family: str | None = Field(
        None, description="Family name of the contact person."
    )
    name_given: list[str] | None = Field(
        None, description="Given names of the contact person, in order."
    )
    name_prefix: list[str] | None = Field(
        None, description="Name prefixes for the contact person."
    )
    name_suffix: list[str] | None = Field(
        None, description="Name suffixes for the contact person."
    )
    name_period_start: str | None = Field(
        None, description="ISO 8601 datetime the contact person's name became valid."
    )
    name_period_end: str | None = Field(
        None,
        description="ISO 8601 datetime the contact person's name stopped being valid.",
    )
    telecom: list[PlainContactTelecom] | None = Field(
        None, description="Contact detail(s) for the contact person."
    )
    address_use: str | None = Field(None, description="home|work|temp|old|billing")
    address_type: str | None = Field(None, description="postal|physical|both")
    address_text: str | None = Field(
        None, description="Full address of the contact person as a display string."
    )
    address_line: list[str] | None = Field(
        None, description="Street address lines for the contact person."
    )
    address_city: str | None = Field(
        None, description="City for the contact person's address."
    )
    address_district: str | None = Field(
        None, description="County/district for the contact person's address."
    )
    address_state: str | None = Field(
        None, description="State for the contact person's address."
    )
    address_postal_code: str | None = Field(
        None, description="Postal code for the contact person's address."
    )
    address_country: str | None = Field(
        None, description="Country for the contact person's address."
    )
    address_period_start: str | None = Field(
        None, description="ISO 8601 datetime the contact person's address became valid."
    )
    address_period_end: str | None = Field(
        None,
        description="ISO 8601 datetime the contact person's address stopped being valid.",
    )
    gender: str | None = Field(None, description="male|female|other|unknown")
    organization_type: str | None = Field(
        None, description="Reference type for the associated organization."
    )
    organization_id: int | None = Field(
        None, description="Public id of the associated Organization."
    )
    organization_display: str | None = Field(
        None, description="Display text for the associated organization."
    )
    organization_identifier_use: str | None = Field(
        None,
        description="Fallback identifier (used when the associated organization "
        "isn't a resource in this system) — usual|official|temp|secondary|old.",
    )
    organization_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    organization_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    organization_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type (e.g. MR, SS)."
    )
    organization_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    organization_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    organization_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    organization_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    organization_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    organization_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it became valid."
    )
    organization_identifier_period_end: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it stopped being valid."
    )
    period_start: str | None = Field(
        None,
        description="ISO 8601 datetime this contact became valid to be contacted regarding the patient.",
    )
    period_end: str | None = Field(
        None,
        description="ISO 8601 datetime this contact stopped being valid to be contacted regarding the patient.",
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


class PlainPatientCommunication(BaseModel):
    """Plain-JSON Patient.communication BackboneElement — a language the patient
    can use for healthcare-related communication."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(None, description="Tenant/ownership organization id.")
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
        None, description="Human-readable name of the language."
    )
    language_text: str | None = Field(
        None, description="Plain-text rendering of the language concept."
    )
    language_user_selected: bool | None = Field(
        None, description="Whether this coding was chosen directly by the user."
    )
    preferred: bool | None = Field(
        None, description="True if this is the patient's preferred language."
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


class PlainPatientGeneralPractitioner(BaseModel):
    """Plain-JSON Patient.generalPractitioner — a reference to the patient's
    nominated primary care provider."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(None, description="Tenant/ownership organization id.")
    reference_type: str | None = Field(
        None, description="Organization|Practitioner|PractitionerRole"
    )
    reference_id: int | None = Field(
        None,
        description="Public id of the referenced Organization/Practitioner/PractitionerRole.",
    )
    reference_display: str | None = Field(
        None, description="Display text for the referenced resource."
    )
    reference_identifier_use: str | None = Field(
        None,
        description="Fallback identifier (used when the referenced resource isn't "
        "in this system) — usual|official|temp|secondary|old.",
    )
    reference_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    reference_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    reference_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type (e.g. MR, SS)."
    )
    reference_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    reference_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    reference_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    reference_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    reference_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    reference_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it became valid."
    )
    reference_identifier_period_end: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it stopped being valid."
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


class PlainPatientLink(BaseModel):
    """Plain-JSON Patient.link — a link to another Patient or RelatedPerson
    resource that concerns the same actual person."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(None, description="Tenant/ownership organization id.")
    other_type: str | None = Field(None, description="Patient|RelatedPerson")
    other_id: int | None = Field(
        None, description="Public id of the linked Patient/RelatedPerson resource."
    )
    other_display: str | None = Field(
        None, description="Display text for the linked resource."
    )
    other_identifier_use: str | None = Field(
        None,
        description="Fallback identifier (used when the linked resource isn't "
        "in this system) — usual|official|temp|secondary|old.",
    )
    other_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    other_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    other_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type (e.g. MR, SS)."
    )
    other_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    other_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    other_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    other_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    other_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    other_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it became valid."
    )
    other_identifier_period_end: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it stopped being valid."
    )
    type: str | None = Field(None, description="replaced-by|replaces|refer|seealso")
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


# ── Plain Patient response ─────────────────────────────────────────────────────


class PlainPatientResponse(BaseModel):
    """Plain-JSON (snake_case) representation of a Patient resource, including all sub-resource arrays."""

    id: int = Field(..., description="Public patient_id.")
    user_id: str | None = Field(
        None, description="Tenant/ownership field — the acting user's id."
    )
    org_id: str | None = Field(
        None, description="Tenant/ownership field — the active organization's id."
    )
    active: bool | None = Field(
        None, description="Whether this patient's record is in active use."
    )
    gender: str | None = Field(None, description="male|female|other|unknown")
    birth_date: str | None = Field(None, description="ISO 8601 date (YYYY-MM-DD).")
    deceased_boolean: bool | None = Field(
        None,
        description="deceased[x] choice — indicates the individual is deceased (boolean form).",
    )
    deceased_datetime: str | None = Field(None, description="ISO 8601 datetime.")
    marital_status_system: str | None = Field(
        None, description="Coding system for the patient's marital status."
    )
    marital_status_version: str | None = Field(
        None, description="Version of the marital-status coding system."
    )
    marital_status_code: str | None = Field(
        None, description="Code for the patient's marital (civil) status."
    )
    marital_status_display: str | None = Field(
        None, description="Display for the marital-status code."
    )
    marital_status_text: str | None = Field(
        None, description="Plain-text rendering of the marital status."
    )
    marital_status_user_selected: bool | None = Field(
        None, description="Whether this coding was chosen directly by the user."
    )
    multiple_birth_boolean: bool | None = Field(
        None,
        description="Whether the patient is part of a multiple birth (boolean form).",
    )
    multiple_birth_integer: int | None = Field(
        None,
        description="The patient's birth order in a multiple birth (integer form).",
    )
    managing_organization_type: str | None = Field(
        None, description="Reference type for the managing organization."
    )
    managing_organization_id: int | None = Field(
        None, description="Public id of the managing Organization."
    )
    managing_organization_display: str | None = Field(
        None, description="Display text for the managing organization."
    )
    managing_organization_identifier_use: str | None = Field(
        None,
        description="Fallback identifier (used when the managing organization "
        "isn't a resource in this system) — usual|official|temp|secondary|old.",
    )
    managing_organization_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    managing_organization_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    managing_organization_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type (e.g. MR, SS)."
    )
    managing_organization_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    managing_organization_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    managing_organization_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    managing_organization_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    managing_organization_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    managing_organization_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it became valid."
    )
    managing_organization_identifier_period_end: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it stopped being valid."
    )
    created_at: str | None = Field(
        None, description="ISO 8601 datetime when record was created."
    )
    updated_at: str | None = Field(
        None, description="ISO 8601 datetime when record was last updated."
    )
    created_by: str | None = Field(
        None, description="Acting-user value recorded as the creator of this record."
    )
    updated_by: str | None = Field(
        None,
        description="Acting-user value recorded as the last updater of this record.",
    )
    name: list[PlainPatientName] | None = Field(
        None, description="Name(s) associated with the patient."
    )
    identifier: list[PlainPatientIdentifier] | None = Field(
        None,
        description="Business identifier(s) for this patient (e.g. MRN, SSN, passport).",
    )
    telecom: list[PlainPatientTelecom] | None = Field(
        None, description="Contact detail(s) (phone, email, etc.) for the patient."
    )
    address: list[PlainPatientAddress] | None = Field(
        None, description="Address(es) for the patient."
    )
    photo: list[PlainPatientPhoto] | None = Field(
        None, description="Image(s) of the patient."
    )
    contact: list[PlainPatientContact] | None = Field(
        None,
        description="Contact party(-ies) (guardian, partner, friend) for the patient.",
    )
    communication: list[PlainPatientCommunication] | None = Field(
        None,
        description="Language(s) the patient can use for healthcare-related communication.",
    )
    general_practitioner: list[PlainPatientGeneralPractitioner] | None = Field(
        None, description="Patient's nominated primary care provider(s)."
    )
    link: list[PlainPatientLink] | None = Field(
        None,
        description="Link(s) to other Patient/RelatedPerson resources concerning the same actual person.",
    )


# ── Plain Patient core-only response (GET /{patient_id}/core) ─────────────────


class PlainPatientCoreResponse(BaseModel):
    """
    Scalar Patient table fields only — backs GET /{patient_id}/core.

    Unlike PlainPatientResponse, this model declares no sub-resource array
    fields at all (not even as always-None Optionals), since that endpoint's
    mapper (to_plain_patient_core()) never returns them — this is what makes
    the OpenAPI/Swagger docs for that route accurate.
    """

    id: int = Field(..., description="Public patient_id.")
    user_id: str | None = Field(
        None, description="Tenant/ownership field — the acting user's id."
    )
    org_id: str | None = Field(
        None, description="Tenant/ownership field — the active organization's id."
    )
    active: bool | None = Field(
        None, description="Whether this patient's record is in active use."
    )
    gender: str | None = Field(None, description="male|female|other|unknown")
    birth_date: str | None = Field(None, description="ISO 8601 date (YYYY-MM-DD).")
    deceased_boolean: bool | None = Field(
        None,
        description="deceased[x] choice — indicates the individual is deceased (boolean form).",
    )
    deceased_datetime: str | None = Field(None, description="ISO 8601 datetime.")
    marital_status_system: str | None = Field(
        None, description="Coding system for the patient's marital status."
    )
    marital_status_version: str | None = Field(
        None, description="Version of the marital-status coding system."
    )
    marital_status_code: str | None = Field(
        None, description="Code for the patient's marital (civil) status."
    )
    marital_status_display: str | None = Field(
        None, description="Display for the marital-status code."
    )
    marital_status_text: str | None = Field(
        None, description="Plain-text rendering of the marital status."
    )
    marital_status_user_selected: bool | None = Field(
        None, description="Whether this coding was chosen directly by the user."
    )
    multiple_birth_boolean: bool | None = Field(
        None,
        description="Whether the patient is part of a multiple birth (boolean form).",
    )
    multiple_birth_integer: int | None = Field(
        None,
        description="The patient's birth order in a multiple birth (integer form).",
    )
    managing_organization_type: str | None = Field(
        None, description="Reference type for the managing organization."
    )
    managing_organization_id: int | None = Field(
        None, description="Public id of the managing Organization."
    )
    managing_organization_display: str | None = Field(
        None, description="Display text for the managing organization."
    )
    managing_organization_identifier_use: str | None = Field(
        None,
        description="Fallback identifier (used when the managing organization "
        "isn't a resource in this system) — usual|official|temp|secondary|old.",
    )
    managing_organization_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    managing_organization_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    managing_organization_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type (e.g. MR, SS)."
    )
    managing_organization_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    managing_organization_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    managing_organization_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    managing_organization_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    managing_organization_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    managing_organization_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it became valid."
    )
    managing_organization_identifier_period_end: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it stopped being valid."
    )
    created_at: str | None = Field(
        None, description="ISO 8601 datetime when record was created."
    )
    updated_at: str | None = Field(
        None, description="ISO 8601 datetime when record was last updated."
    )
    created_by: str | None = Field(
        None, description="Acting-user value recorded as the creator of this record."
    )
    updated_by: str | None = Field(
        None,
        description="Acting-user value recorded as the last updater of this record.",
    )


# ── Paginated response ─────────────────────────────────────────────────────────


class PaginatedPatientResponse(BaseModel):
    """Plain-JSON paginated envelope for GET / (list patients)."""

    total: int = Field(..., description="Total number of matching patients.")
    limit: int = Field(..., description="Page size requested.")
    offset: int = Field(..., description="Number of records skipped.")
    data: list[PlainPatientResponse] = Field(
        ..., description="Array of plain-JSON Patient objects."
    )


# ── Sub-resource list responses ────────────────────────────────────────────────


class PatientNamesListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/names."""

    data: list[PlainPatientName] = Field(
        ..., description="HumanName entries for the patient."
    )
    total: int = Field(..., description="Total count of name entries.")


class PatientIdentifiersListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/identifiers."""

    data: list[PlainPatientIdentifier] = Field(
        ..., description="Business identifier entries for the patient."
    )
    total: int = Field(..., description="Total count of identifier entries.")


class PatientTelecomListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/telecom."""

    data: list[PlainPatientTelecom] = Field(
        ..., description="Contact point entries for the patient."
    )
    total: int = Field(..., description="Total count of contact point entries.")


class PatientAddressesListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/addresses."""

    data: list[PlainPatientAddress] = Field(
        ..., description="Address entries for the patient."
    )
    total: int = Field(..., description="Total count of address entries.")


class PatientPhotosListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/photos."""

    data: list[PlainPatientPhoto] = Field(
        ..., description="Photo attachment entries for the patient."
    )
    total: int = Field(..., description="Total count of photo entries.")


class PatientContactsListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/contacts."""

    data: list[PlainPatientContact] = Field(
        ..., description="Contact entries for the patient."
    )
    total: int = Field(..., description="Total count of contact entries.")


class PatientCommunicationsListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/communications."""

    data: list[PlainPatientCommunication] = Field(
        ..., description="Communication-language entries for the patient."
    )
    total: int = Field(..., description="Total count of communication entries.")


class PatientGeneralPractitionersListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/general-practitioners."""

    data: list[PlainPatientGeneralPractitioner] = Field(
        ..., description="General-practitioner reference entries for the patient."
    )
    total: int = Field(
        ..., description="Total count of general practitioner references."
    )


class PatientLinksListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/links."""

    data: list[PlainPatientLink] = Field(..., description="Patient link entries.")
    total: int = Field(..., description="Total count of patient link entries.")


# ── FHIR sub-resource list responses ──────────────────────────────────────────


class FHIRPatientNameListItem(FHIRHumanName):
    """FHIRHumanName plus the internal row id, for the GET /{patient_id}/names list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientNamesListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/names."""

    data: list[FHIRPatientNameListItem] = Field(
        ..., description="HumanName entries for the patient."
    )
    total: int = Field(..., description="Total count of name entries.")


class FHIRPatientIdentifierListItem(FHIRIdentifier):
    """FHIRIdentifier plus the internal row id, for the GET /{patient_id}/identifiers list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientIdentifiersListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/identifiers."""

    data: list[FHIRPatientIdentifierListItem] = Field(
        ..., description="Business identifier entries for the patient."
    )
    total: int = Field(..., description="Total count of identifier entries.")


class FHIRPatientTelecomListItem(FHIRContactPoint):
    """FHIRContactPoint plus the internal row id, for the GET /{patient_id}/telecom list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientTelecomListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/telecom."""

    data: list[FHIRPatientTelecomListItem] = Field(
        ..., description="Contact point entries for the patient."
    )
    total: int = Field(..., description="Total count of contact point entries.")


class FHIRPatientAddressListItem(FHIRAddress):
    """FHIRAddress plus the internal row id, for the GET /{patient_id}/addresses list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientAddressesListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/addresses."""

    data: list[FHIRPatientAddressListItem] = Field(
        ..., description="Address entries for the patient."
    )
    total: int = Field(..., description="Total count of address entries.")


class FHIRPatientPhotoListItem(FHIRAttachment):
    """FHIRAttachment plus the internal row id, for the GET /{patient_id}/photos list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientPhotosListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/photos."""

    data: list[FHIRPatientPhotoListItem] = Field(
        ..., description="Photo attachment entries for the patient."
    )
    total: int = Field(..., description="Total count of photo entries.")


class FHIRPatientContactListItem(FHIRPatientContact):
    """FHIRPatientContact plus the internal row id, for the GET /{patient_id}/contacts list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientContactsListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/contacts."""

    data: list[FHIRPatientContactListItem] = Field(
        ..., description="Contact entries for the patient."
    )
    total: int = Field(..., description="Total count of contact entries.")


class FHIRPatientCommunicationListItem(FHIRPatientCommunication):
    """FHIRPatientCommunication plus the internal row id, for the GET /{patient_id}/communications list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientCommunicationsListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/communications."""

    data: list[FHIRPatientCommunicationListItem] = Field(
        ..., description="Communication-language entries for the patient."
    )
    total: int = Field(..., description="Total count of communication entries.")


class FHIRPatientGeneralPractitionerListItem(FHIRReference):
    """FHIRReference plus the internal row id, for the GET /{patient_id}/general-practitioners list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientGeneralPractitionersListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/general-practitioners."""

    data: list[FHIRPatientGeneralPractitionerListItem] = Field(
        ..., description="General-practitioner reference entries for the patient."
    )
    total: int = Field(
        ..., description="Total count of general practitioner references."
    )


class FHIRPatientLinkListItem(FHIRPatientLink):
    """FHIRPatientLink plus the internal row id, for the GET /{patient_id}/links list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientLinksListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/links."""

    data: list[FHIRPatientLinkListItem] = Field(
        ..., description="Patient link entries."
    )
    total: int = Field(..., description="Total count of patient link entries.")
