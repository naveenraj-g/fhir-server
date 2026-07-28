from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IdentifierUse
from app.models.patient.enums import (
    AddressType,
    AddressUse,
    ContactPointSystem,
    ContactPointUse,
    HumanNameUse,
    PatientGender,
    PatientGeneralPractitionerType,
    PatientLinkOtherType,
    PatientLinkType,
)

# ── Sub-resource create schemas ────────────────────────────────────────────────


class NameCreate(BaseModel):
    """FHIR R4 HumanName — a name associated with the patient."""

    model_config = ConfigDict(extra="forbid")
    use: HumanNameUse | None = Field(
        None,
        description=(
            "Identifies the purpose of this name. "
            "usual|official|temp|nickname|anonymous|old|maiden."
        ),
    )
    text: str | None = Field(
        None,
        description="Text representation of the full name, as it would normally be displayed.",
    )
    family: str | None = Field(
        None, description="Family name (often called 'surname')."
    )
    given: list[str] | None = Field(
        None,
        description="Given names (not always 'first'). Includes middle names — order matters.",
    )
    prefix: list[str] | None = Field(
        None, description="Parts that come before the name (e.g. Mr., Dr., titles)."
    )
    suffix: list[str] | None = Field(
        None,
        description="Parts that come after the name (e.g. Jr., MD, qualifications).",
    )
    period_start: datetime | None = Field(
        None, description="Start of the period during which this name was/is in use."
    )
    period_end: datetime | None = Field(
        None, description="End of the period during which this name was/is in use."
    )


class IdentifierCreate(BaseModel):
    """FHIR R4 Identifier — a business identifier for this patient (e.g. MRN, SSN, passport)."""

    model_config = ConfigDict(extra="forbid")
    use: IdentifierUse | None = Field(
        None,
        description=(
            "The purpose of this identifier. usual|official|temp|secondary|old."
        ),
    )
    type_system: str | None = Field(
        None,
        description=(
            "Identifier.type.coding.system — coding system that defines the "
            "identifier type (e.g. http://terminology.hl7.org/CodeSystem/v2-0203)."
        ),
    )
    type_version: str | None = Field(
        None,
        description="Identifier.type.coding.version — version of the identifier-type coding system.",
    )
    type_code: str | None = Field(
        None,
        description="Identifier.type.coding.code — code for the identifier type (e.g. MR, SS, PPN).",
    )
    type_display: str | None = Field(
        None,
        description="Identifier.type.coding.display — human-readable display for the identifier-type code.",
    )
    type_text: str | None = Field(
        None,
        description="Identifier.type.text — plain-text rendering of the identifier-type CodeableConcept.",
    )
    type_user_selected: bool | None = Field(
        None,
        description="Identifier.type.coding.userSelected — whether this identifier-type coding was chosen directly by the user.",
    )
    system: str = Field(
        ...,
        description="The namespace (a URI) that identifies the scope this identifier's value is unique within.",
    )
    value: str = Field(
        ..., description="The identifier value itself, unique within the given system."
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the period during which this identifier is/was valid for use.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period during which this identifier is/was valid for use.",
    )
    assigner: str | None = Field(
        None,
        description="Identifier.assigner — display name of the organization that issued this identifier.",
    )


class TelecomCreate(BaseModel):
    """FHIR R4 ContactPoint — a contact detail (phone, email, etc.) for the patient."""

    model_config = ConfigDict(extra="forbid")
    system: ContactPointSystem = Field(
        ...,
        description="Telecommunications form for this contact point. phone|fax|email|pager|url|sms|other.",
    )
    value: str = Field(
        ...,
        description="The actual contact point details (e.g. a phone number or email address).",
    )
    use: ContactPointUse | None = Field(
        None, description="Purpose of this contact point. home|work|temp|old|mobile."
    )
    rank: int | None = Field(
        None,
        ge=1,
        description="Preferred order of use among an individual's contact points — 1 indicates the most preferred.",
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the period during which this contact point was/is in use.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period during which this contact point was/is in use.",
    )


class AddressCreate(BaseModel):
    """FHIR R4 Address — a postal or physical address for the patient."""

    model_config = ConfigDict(extra="forbid")
    use: AddressUse | None = Field(
        None, description="The purpose of this address. home|work|temp|old|billing."
    )
    type: AddressType | None = Field(
        None,
        description="Distinguishes physical locations from mailing addresses. postal|physical|both.",
    )
    text: str | None = Field(
        None,
        description="Text representation of the address, as it would normally be displayed on a mailing label.",
    )
    line: list[str] | None = Field(
        None,
        description="Street name, number, direction, P.O. Box, or similar — one entry per address line, in order.",
    )
    city: str | None = Field(
        None, description="Name of the city, town, suburb, village, or other community."
    )
    district: str | None = Field(None, description="County or administrative district.")
    state: str | None = Field(
        None, description="Sub-unit of country — state, province, etc."
    )
    postal_code: str | None = Field(None, description="Postal/ZIP code for the area.")
    country: str | None = Field(
        None, description="Country — e.g. an ISO 3166 2- or 3-letter code."
    )
    period_start: datetime | None = Field(
        None, description="Start of the period during which this address was/is in use."
    )
    period_end: datetime | None = Field(
        None, description="End of the period during which this address was/is in use."
    )


class PhotoCreate(BaseModel):
    """FHIR R4 Attachment — an image of the patient."""

    model_config = ConfigDict(extra="forbid")
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
    creation: datetime | None = Field(
        None, description="Date the image attachment was first created."
    )


class ContactRelationshipCreate(BaseModel):
    """FHIR R4 CodeableConcept — the kind of relationship a Patient.contact has to the patient."""

    model_config = ConfigDict(extra="forbid")
    coding_system: str | None = Field(
        None,
        description="Coding.system — coding system that defines this relationship code.",
    )
    coding_version: str | None = Field(
        None, description="Coding.version — version of the coding system."
    )
    coding_code: str | None = Field(
        None,
        description="Coding.code — code for the nature of the relationship (e.g. C, N, MTH, FTH).",
    )
    coding_display: str | None = Field(
        None,
        description="Coding.display — human-readable display for the relationship code.",
    )
    text: str | None = Field(
        None, description="Plain-text rendering of the relationship CodeableConcept."
    )
    coding_user_selected: bool | None = Field(
        None,
        description="Coding.userSelected — whether this coding was chosen directly by the user.",
    )


class ContactTelecomCreate(BaseModel):
    """FHIR R4 ContactPoint — a contact detail for the patient's contact person."""

    model_config = ConfigDict(extra="forbid")
    system: ContactPointSystem | None = Field(
        None,
        description="Telecommunications form for this contact point. phone|fax|email|pager|url|sms|other.",
    )
    value: str | None = Field(
        None,
        description="The actual contact point details (e.g. a phone number or email address).",
    )
    use: ContactPointUse | None = Field(
        None, description="Purpose of this contact point. home|work|temp|old|mobile."
    )
    rank: int | None = Field(
        None,
        ge=1,
        description="Preferred order of use — 1 indicates the most preferred.",
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the period during which this contact point was/is in use.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period during which this contact point was/is in use.",
    )


class ContactCreate(BaseModel):
    """FHIR R4 Patient.contact BackboneElement — a contact party (guardian, partner,
    friend, etc.) for the patient. SHALL have contact details or an organization reference."""

    model_config = ConfigDict(extra="forbid")
    # relationship (0..*) CodeableConcept → grandchild table
    relationship: list[ContactRelationshipCreate] | None = Field(
        None, description="The kind(s) of relationship this contact has to the patient."
    )
    # name (0..1 HumanName) — flattened
    name_use: HumanNameUse | None = Field(
        None,
        description="HumanName.use for the contact person's name. usual|official|temp|nickname|anonymous|old|maiden.",
    )
    name_text: str | None = Field(
        None,
        description="HumanName.text — full name of the contact person as a display string.",
    )
    name_family: str | None = Field(
        None, description="HumanName.family — the contact person's family name."
    )
    name_given: list[str] | None = Field(
        None,
        description="HumanName.given — the contact person's given names, in order.",
    )
    name_prefix: list[str] | None = Field(
        None, description="HumanName.prefix — name prefixes (Mr., Dr., etc.)."
    )
    name_suffix: list[str] | None = Field(
        None, description="HumanName.suffix — name suffixes (Jr., MD, etc.)."
    )
    name_period_start: datetime | None = Field(
        None,
        description="HumanName.period.start — when the contact person's name became valid.",
    )
    name_period_end: datetime | None = Field(
        None,
        description="HumanName.period.end — when the contact person's name stopped being valid.",
    )
    # telecom (0..*) ContactPoint → grandchild table
    telecom: list[ContactTelecomCreate] | None = Field(
        None,
        description="Contact detail(s) (phone, email, etc.) for the contact person.",
    )
    # address (0..1 Address) — flattened
    address_use: AddressUse | None = Field(
        None,
        description="Address.use for the contact person's address. home|work|temp|old|billing.",
    )
    address_type: AddressType | None = Field(
        None,
        description="Address.type for the contact person's address. postal|physical|both.",
    )
    address_text: str | None = Field(
        None,
        description="Address.text — full address of the contact person as a display string.",
    )
    address_line: list[str] | None = Field(
        None,
        description="Address.line — street address lines for the contact person, in order.",
    )
    address_city: str | None = Field(
        None, description="Address.city for the contact person."
    )
    address_district: str | None = Field(
        None, description="Address.district (county) for the contact person."
    )
    address_state: str | None = Field(
        None, description="Address.state for the contact person."
    )
    address_postal_code: str | None = Field(
        None, description="Address.postalCode for the contact person."
    )
    address_country: str | None = Field(
        None, description="Address.country for the contact person."
    )
    address_period_start: datetime | None = Field(
        None,
        description="Address.period.start — when the contact person's address became valid.",
    )
    address_period_end: datetime | None = Field(
        None,
        description="Address.period.end — when the contact person's address stopped being valid.",
    )
    # other scalar fields
    gender: PatientGender | None = Field(
        None,
        description="Administrative gender of the contact person. male|female|other|unknown.",
    )
    organization: str | None = Field(
        None,
        description=(
            "Reference(Organization) associated with the contact, as a FHIR reference "
            "string (e.g. 'Organization/100'). Required if no contact name/relationship is given."
        ),
    )
    organization_display: str | None = Field(
        None, description="Display text for the referenced organization."
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the period during which this contact is valid to be contacted regarding the patient.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period during which this contact is valid to be contacted regarding the patient.",
    )


class CommunicationCreate(BaseModel):
    """FHIR R4 Patient.communication BackboneElement — a language the patient can use
    for healthcare-related communication."""

    model_config = ConfigDict(extra="forbid")
    language_system: str | None = Field(
        None,
        description=(
            "CodeableConcept.coding.system for the language (e.g. urn:ietf:bcp:47)."
        ),
    )
    language_version: str | None = Field(
        None,
        description="CodeableConcept.coding.version — version of the language coding system.",
    )
    language_code: str = Field(
        ...,
        description="ISO-639-1 language code (e.g. en, fr, de), optionally region-qualified (e.g. en-US).",
    )
    language_display: str | None = Field(
        None,
        description="CodeableConcept.coding.display — human-readable name of the language.",
    )
    language_text: str | None = Field(
        None,
        description="CodeableConcept.text — plain-text rendering of the language concept.",
    )
    language_user_selected: bool | None = Field(
        None,
        description="CodeableConcept.coding.userSelected — whether this coding was chosen directly by the user.",
    )
    preferred: bool | None = Field(
        None,
        description="True if this language is the patient's preferred language for communication.",
    )


class GeneralPractitionerCreate(BaseModel):
    """FHIR R4 Patient.generalPractitioner — a reference to the patient's nominated
    primary care provider."""

    model_config = ConfigDict(extra="forbid")
    reference_type: PatientGeneralPractitionerType = Field(
        ...,
        description="Resource type of the referenced practitioner. Organization|Practitioner|PractitionerRole.",
    )
    reference_id: int = Field(
        ...,
        description="Public id of the referenced Organization/Practitioner/PractitionerRole.",
    )
    reference_display: str | None = Field(
        None, description="Display text for the referenced resource."
    )


class LinkCreate(BaseModel):
    """FHIR R4 Patient.link — a link to another Patient or RelatedPerson resource
    that concerns the same actual person."""

    model_config = ConfigDict(extra="forbid")
    other_type: PatientLinkOtherType = Field(
        ..., description="Resource type of the linked resource. Patient|RelatedPerson."
    )
    other_id: int = Field(
        ..., description="Public id of the linked Patient/RelatedPerson resource."
    )
    other_display: str | None = Field(
        None, description="Display text for the linked resource."
    )
    type: PatientLinkType = Field(
        ...,
        description=(
            "The type of link between this patient resource and the other. "
            "replaced-by|replaces|refer|seealso."
        ),
    )


# ── Sub-resource patch schemas ────────────────────────────────────────────────


class NamePatch(BaseModel):
    """Partial update to a HumanName entry — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")
    use: HumanNameUse | None = Field(
        None, description="usual|official|temp|nickname|anonymous|old|maiden."
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
    period_start: datetime | None = Field(
        None, description="Start of period when this name was valid."
    )
    period_end: datetime | None = Field(
        None, description="End of period when this name was valid."
    )


class IdentifierPatch(BaseModel):
    """Partial update to a business identifier — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")
    use: IdentifierUse | None = Field(
        None, description="usual|official|temp|secondary|old."
    )
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
    period_start: datetime | None = Field(
        None, description="Start of identifier validity period."
    )
    period_end: datetime | None = Field(
        None, description="End of identifier validity period."
    )
    assigner: str | None = Field(
        None, description="Display name of the issuing organization."
    )


class TelecomPatch(BaseModel):
    """Partial update to a contact point — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")
    system: ContactPointSystem | None = Field(
        None, description="phone|fax|email|pager|url|sms|other."
    )
    value: str | None = Field(
        None, description="Contact point details (phone number, email address, etc.)."
    )
    use: ContactPointUse | None = Field(None, description="home|work|temp|old|mobile.")
    rank: int | None = Field(
        None, ge=1, description="Preferred order — 1 indicates the most preferred."
    )
    period_start: datetime | None = Field(
        None, description="Start of period when this contact point was valid."
    )
    period_end: datetime | None = Field(
        None, description="End of period when this contact point was valid."
    )


class AddressPatch(BaseModel):
    """Partial update to an address — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")
    use: AddressUse | None = Field(None, description="home|work|temp|old|billing.")
    type: AddressType | None = Field(None, description="postal|physical|both.")
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
    period_start: datetime | None = Field(
        None, description="Start of period when this address was valid."
    )
    period_end: datetime | None = Field(
        None, description="End of period when this address was valid."
    )


class PhotoPatch(BaseModel):
    """Partial update to a photo attachment — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")
    content_type: str | None = Field(None, description="MIME type (e.g. image/png).")
    language: str | None = Field(None, description="BCP-47 language code.")
    data: str | None = Field(None, description="Base64-encoded image data.")
    url: str | None = Field(None, description="URL where the image can be retrieved.")
    size: int | None = Field(None, description="Size in bytes, after base64 decoding.")
    hash: str | None = Field(
        None, description="Base64-encoded SHA-1 hash of the image data."
    )
    title: str | None = Field(None, description="Label or display title.")
    creation: datetime | None = Field(None, description="When the image was created.")


class ContactPatch(BaseModel):
    """Partial update to a Patient.contact BackboneElement. If `relationship` or
    `telecom` is supplied, the entire corresponding sub-list is replaced."""

    model_config = ConfigDict(extra="forbid")
    relationship: list[ContactRelationshipCreate] | None = Field(
        None,
        description="The kind(s) of relationship this contact has to the patient — replaces the full list if supplied.",
    )
    name_use: HumanNameUse | None = Field(
        None, description="usual|official|temp|nickname|anonymous|old|maiden."
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
    name_period_start: datetime | None = Field(
        None, description="When the contact person's name became valid."
    )
    name_period_end: datetime | None = Field(
        None, description="When the contact person's name stopped being valid."
    )
    telecom: list[ContactTelecomCreate] | None = Field(
        None,
        description="Contact detail(s) for the contact person — replaces the full list if supplied.",
    )
    address_use: AddressUse | None = Field(
        None, description="home|work|temp|old|billing."
    )
    address_type: AddressType | None = Field(None, description="postal|physical|both.")
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
    address_period_start: datetime | None = Field(
        None, description="When the contact person's address became valid."
    )
    address_period_end: datetime | None = Field(
        None, description="When the contact person's address stopped being valid."
    )
    gender: PatientGender | None = Field(None, description="male|female|other|unknown.")
    organization: str | None = Field(
        None, description="FHIR reference, e.g. 'Organization/100'."
    )
    organization_display: str | None = Field(
        None, description="Display text for the referenced organization."
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the period during which this contact is valid to be contacted.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period during which this contact is valid to be contacted.",
    )


class CommunicationPatch(BaseModel):
    """Partial update to a communication-language entry — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")
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


class GeneralPractitionerPatch(BaseModel):
    """Partial update to a general-practitioner reference — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")
    reference_type: PatientGeneralPractitionerType | None = Field(
        None, description="Organization|Practitioner|PractitionerRole."
    )
    reference_id: int | None = Field(
        None, description="Public id of the referenced resource."
    )
    reference_display: str | None = Field(
        None, description="Display text for the referenced resource."
    )


class LinkPatch(BaseModel):
    """Partial update to a patient link entry — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")
    other_type: PatientLinkOtherType | None = Field(
        None, description="Patient|RelatedPerson."
    )
    other_id: int | None = Field(None, description="Public id of the linked resource.")
    other_display: str | None = Field(
        None, description="Display text for the linked resource."
    )
    type: PatientLinkType | None = Field(
        None, description="replaced-by|replaces|refer|seealso."
    )


# ── Patient create / patch ─────────────────────────────────────────────────────


class PatientCreateSchema(BaseModel):
    """Core scalar fields for creating a FHIR R4 Patient resource. Sub-resource
    arrays (name, identifier, telecom, etc.) are added via dedicated endpoints —
    see PatientFullCreateSchema to create everything in one request."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-uuid-123",
                "org_id": "org-uuid-456",
                "active": True,
                "gender": "male",
                "birth_date": "1985-04-12",
                "deceased_boolean": False,
                "marital_status_code": "M",
                "marital_status_system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                "marital_status_display": "Married",
            }
        },
    )

    user_id: str | None = Field(
        None,
        description="Tenant/ownership field forwarded by the GraphQL gateway — the acting user's id.",
    )
    org_id: str = Field(
        ...,
        description="Tenant/ownership field forwarded by the GraphQL gateway — the active organization's id.",
    )
    active: bool | None = Field(
        True, description="Whether this patient's record is in active use."
    )
    gender: PatientGender | None = Field(
        None, description="Administrative gender. male|female|other|unknown."
    )
    birth_date: date | None = Field(
        None, description="The date of birth for the individual."
    )
    deceased_boolean: bool | None = Field(
        None,
        description="deceased[x] choice — indicates the individual is deceased (boolean form).",
    )
    deceased_datetime: datetime | None = Field(
        None,
        description="deceased[x] choice — the date/time the individual died (dateTime form).",
    )
    marital_status_system: str | None = Field(
        None,
        description="maritalStatus.coding.system — coding system for the patient's marital status.",
    )
    marital_status_version: str | None = Field(
        None,
        description="maritalStatus.coding.version — version of the marital-status coding system.",
    )
    marital_status_code: str | None = Field(
        None,
        description="maritalStatus.coding.code — code for the patient's marital (civil) status.",
    )
    marital_status_display: str | None = Field(
        None,
        description="maritalStatus.coding.display — human-readable display for the marital-status code.",
    )
    marital_status_text: str | None = Field(
        None,
        description="maritalStatus.text — plain-text rendering of the marital status.",
    )
    marital_status_user_selected: bool | None = Field(
        None,
        description="maritalStatus.coding.userSelected — whether this coding was chosen directly by the user.",
    )
    multiple_birth_boolean: bool | None = Field(
        None,
        description="multipleBirth[x] choice — whether the patient is part of a multiple birth (boolean form).",
    )
    multiple_birth_integer: int | None = Field(
        None,
        description="multipleBirth[x] choice — the patient's birth order in a multiple birth (integer form).",
    )
    managing_organization: str | None = Field(
        None,
        description=(
            "managingOrganization — Reference(Organization) that is the custodian of "
            "the patient record, as a FHIR reference string, e.g. 'Organization/100'."
        ),
    )
    managing_organization_display: str | None = Field(
        None,
        description="managingOrganization.display — display text for the managing organization.",
    )


class PatientPatchSchema(BaseModel):
    """Partial update to a Patient's core scalar fields. Only supplied fields are
    written; sub-resources are managed via dedicated endpoints."""

    model_config = ConfigDict(extra="forbid")

    active: bool | None = Field(
        None, description="Whether this patient's record is in active use."
    )
    gender: PatientGender | None = Field(None, description="male|female|other|unknown.")
    birth_date: date | None = Field(
        None, description="The date of birth for the individual."
    )
    deceased_boolean: bool | None = Field(
        None,
        description="deceased[x] choice — indicates the individual is deceased (boolean form).",
    )
    deceased_datetime: datetime | None = Field(
        None,
        description="deceased[x] choice — the date/time the individual died (dateTime form).",
    )
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
    managing_organization: str | None = Field(
        None, description="FHIR reference, e.g. 'Organization/100'."
    )
    managing_organization_display: str | None = Field(
        None, description="Display text for the managing organization."
    )


class PatientFullCreateSchema(PatientCreateSchema):
    """Creates a Patient and any combination of sub-resources atomically in a
    single DB transaction. All sub-resource lists are optional."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-uuid-123",
                "org_id": "org-uuid-456",
                "active": True,
                "gender": "male",
                "birth_date": "1985-04-12",
                "names": [{"use": "official", "family": "Doe", "given": ["John"]}],
                "identifiers": [
                    {"value": "MRN-123456", "system": "http://hospital.com/mrn"}
                ],
                "telecom": [
                    {"system": "phone", "value": "+1-555-123-4567", "use": "mobile"}
                ],
                "addresses": [
                    {"use": "home", "city": "New York", "state": "NY", "country": "USA"}
                ],
                "communications": [{"language_code": "en", "preferred": True}],
            }
        },
    )
    names: list[NameCreate] | None = Field(
        None, description="HumanName entries for the patient."
    )
    identifiers: list[IdentifierCreate] | None = Field(
        None,
        description="Business identifiers (MRN, SSN, passport, etc.) for the patient.",
    )
    telecom: list[TelecomCreate] | None = Field(
        None, description="Contact points (phone, email, etc.) for the patient."
    )
    addresses: list[AddressCreate] | None = Field(
        None, description="Addresses for the patient."
    )
    photos: list[PhotoCreate] | None = Field(
        None, description="Image attachments of the patient."
    )
    contacts: list[ContactCreate] | None = Field(
        None,
        description="Contact parties (guardian, next-of-kin, emergency contact) for the patient.",
    )
    communications: list[CommunicationCreate] | None = Field(
        None,
        description="Languages the patient can use for healthcare-related communication.",
    )
    general_practitioners: list[GeneralPractitionerCreate] | None = Field(
        None,
        description="References to the patient's nominated primary care provider(s).",
    )
    links: list[LinkCreate] | None = Field(
        None,
        description="Links to other Patient/RelatedPerson resources concerning the same actual person.",
    )


class PatientFullPatchSchema(PatientPatchSchema):
    """Patches a Patient's scalar fields and, for each sub-resource list that is
    supplied (even `[]`), atomically replaces it. Lists that are omitted are left
    untouched."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "active": True,
                "gender": "male",
                "names": [{"use": "official", "family": "Doe", "given": ["John"]}],
                "telecom": [
                    {"system": "phone", "value": "+1-555-999-0000", "use": "mobile"}
                ],
                "communications": [{"language_code": "en", "preferred": True}],
            }
        },
    )
    names: list[NameCreate] | None = Field(
        None,
        description="HumanName entries for the patient — replaces the full list if supplied.",
    )
    identifiers: list[IdentifierCreate] | None = Field(
        None,
        description="Business identifiers for the patient — replaces the full list if supplied.",
    )
    telecom: list[TelecomCreate] | None = Field(
        None,
        description="Contact points for the patient — replaces the full list if supplied.",
    )
    addresses: list[AddressCreate] | None = Field(
        None,
        description="Addresses for the patient — replaces the full list if supplied.",
    )
    photos: list[PhotoCreate] | None = Field(
        None,
        description="Image attachments of the patient — replaces the full list if supplied.",
    )
    contacts: list[ContactCreate] | None = Field(
        None,
        description="Contact parties for the patient — replaces the full list if supplied.",
    )
    communications: list[CommunicationCreate] | None = Field(
        None,
        description="Communication languages for the patient — replaces the full list if supplied.",
    )
    general_practitioners: list[GeneralPractitionerCreate] | None = Field(
        None,
        description="General-practitioner references — replaces the full list if supplied.",
    )
    links: list[LinkCreate] | None = Field(
        None, description="Patient links — replaces the full list if supplied."
    )
