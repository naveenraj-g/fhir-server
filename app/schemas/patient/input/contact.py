from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IdentifierUse
from app.models.patient.enums import (
    AddressType,
    AddressUse,
    ContactPointSystem,
    ContactPointUse,
    HumanNameUse,
    PatientGender,
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
    friend, etc.) for the patient. Per pat-1, SHALL have at least one of name,
    telecom, address, or an organization reference."""

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
            "string (e.g. 'Organization/100'). Per pat-1, required if none of name, "
            "telecom, or address is given."
        ),
    )
    organization_display: str | None = Field(
        None, description="Display text for the referenced organization."
    )
    organization_identifier_use: IdentifierUse | None = Field(
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
    organization_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — when it became valid."
    )
    organization_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — when it stopped being valid."
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the period during which this contact is valid to be contacted regarding the patient.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period during which this contact is valid to be contacted regarding the patient.",
    )


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
    organization_identifier_use: IdentifierUse | None = Field(
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
    organization_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — when it became valid."
    )
    organization_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — when it stopped being valid."
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the period during which this contact is valid to be contacted.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period during which this contact is valid to be contacted.",
    )
