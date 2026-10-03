from pydantic import BaseModel, Field

from app.schemas.common.fhir import (
    FHIRAddress,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRHumanName,
)

from ._shared import PlainOrganizationCoding, _AuditFields


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
    purpose_codings: list[PlainOrganizationCoding] | None = Field(
        None, description="Coding(s) for this contact's purpose."
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
