from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput, ContactPointInput
from app.schemas.enums import AddressType, AddressUse, AdministrativeGender, HumanNameUse, IdentifierUse


class PatientContactRelationshipInput(BaseModel):
    """Patient.contact.relationship — the kind of relationship (CodeableConcept)."""

    model_config = ConfigDict(extra="forbid")
    text: str | None = Field(None, description="Plain text representation of the relationship.")
    coding: list[CodingInput] | None = Field(
        None, description="Coding(s) identifying the nature of the relationship."
    )


class PatientContactInput(BaseModel):
    """Patient.contact — a contact party (e.g. guardian, partner, friend) for the patient (BackboneElement)."""

    model_config = ConfigDict(extra="forbid")
    relationship: list[PatientContactRelationshipInput] | None = Field(
        None, description="The nature of the relationship between the patient and the contact person."
    )
    gender: AdministrativeGender | None = Field(
        None, description="Administrative Gender — male|female|other|unknown."
    )

    # name (0..1 HumanName) flattened
    name_use: HumanNameUse | None = Field(
        None, description="Identifies the purpose for this contact name."
    )
    name_text: str | None = Field(
        None, description="Specifies the entire contact name as it should be displayed."
    )
    name_family: str | None = Field(
        None, description="Family name / surname of the contact."
    )
    name_given: list[str] | None = Field(None, description="Given name(s) of the contact.")
    name_prefix: list[str] | None = Field(None, description="Title/prefix of the contact.")
    name_suffix: list[str] | None = Field(None, description="Suffix of the contact.")
    name_period_start: datetime | None = Field(
        None, description="Start of name validity period."
    )
    name_period_end: datetime | None = Field(
        None, description="End of name validity period."
    )

    # telecom (0..* ContactPoint)
    telecom: list[ContactPointInput] | None = Field(
        None, description="Contact details for the person."
    )

    # address (0..1 Address) flattened
    address_use: AddressUse | None = Field(
        None, description="home|work|temp|old|billing."
    )
    address_type: AddressType | None = Field(
        None, description="postal|physical|both."
    )
    address_text: str | None = Field(
        None, description="Entire address formatted as text."
    )
    address_line: list[str] | None = Field(
        None, description="Street address lines."
    )
    address_city: str | None = Field(None, description="City / town / suburb.")
    address_district: str | None = Field(None, description="District / county.")
    address_state: str | None = Field(None, description="State / province.")
    address_postal_code: str | None = Field(None, description="Postal / ZIP code.")
    address_country: str | None = Field(None, description="Country name / code.")
    address_period_start: datetime | None = Field(
        None, description="Start of address validity period."
    )
    address_period_end: datetime | None = Field(
        None, description="End of address validity period."
    )

    # period (0..1 Period)
    period_start: datetime | None = Field(
        None, description="Start of the period during which this contact person is valid."
    )
    period_end: datetime | None = Field(
        None, description="End of the period during which this contact person is valid."
    )

    # organization (0..1 Reference(Organization))
    organization: str | None = Field(
        None,
        description="Organization on behalf of which the contact is acting (e.g. 'Organization/190001').",
    )
    organization_display: str | None = Field(
        None, description="Display narrative for the organization reference."
    )
    organization_identifier_system: str | None = Field(
        None, description="Logical-reference fallback — identifier namespace URL."
    )
    organization_identifier_value: str | None = Field(
        None, description="Logical-reference fallback — identifier value."
    )
    organization_identifier_use: IdentifierUse | None = Field(
        None, description="Logical-reference fallback — identifier use."
    )
    organization_identifier_type_text: str | None = Field(
        None, description="Logical-reference fallback — identifier type text."
    )
