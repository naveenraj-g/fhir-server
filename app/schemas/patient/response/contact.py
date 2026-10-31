from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    AuditFields,
    FHIRAddress,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRHumanName,
    FHIRPeriod,
    FHIRReference,
    PlainCodingRow,
    PlainContactPointRow,
)


class FHIRPatientContact(BaseModel):
    relationship: list[FHIRCodeableConcept] | None = Field(
        None, description="The nature of the relationship."
    )
    name: FHIRHumanName | None = Field(
        None, description="A name associated with the contact person."
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None, description="A contact detail for the person."
    )
    address: FHIRAddress | None = Field(
        None, description="Address for the contact person."
    )
    gender: str | None = Field(
        None, description="male | female | other | unknown"
    )
    organization: FHIRReference | None = Field(
        None, description="Organization that is associated with the contact."
    )
    period: FHIRPeriod | None = Field(
        None, description="The period during which this contact is valid."
    )


class PlainPatientContactRelationship(AuditFields):
    id: int = Field(..., description="Internal row ID.")
    text: str | None = Field(None, description="Relationship text description.")
    codings: list[PlainCodingRow] | None = Field(
        None, description="Coding(s) for the relationship."
    )


class PlainPatientContact(AuditFields):
    id: int = Field(..., description="Internal row ID.")
    relationships: list[PlainPatientContactRelationship] | None = Field(
        None, description="Relationship(s) of this contact to the patient."
    )
    gender: str | None = Field(
        None, description="Administrative Gender — male|female|other|unknown."
    )
    name_use: str | None = Field(None, description="Name purpose.")
    name_text: str | None = Field(None, description="Text representation of the name.")
    name_family: str | None = Field(None, description="Family name.")
    name_given: list[str] | None = Field(None, description="Given name(s).")
    name_prefix: list[str] | None = Field(None, description="Title/prefix.")
    name_suffix: list[str] | None = Field(None, description="Suffix.")
    name_period_start: str | None = Field(None, description="Start of name period.")
    name_period_end: str | None = Field(None, description="End of name period.")
    telecom: list[PlainContactPointRow] | None = Field(
        None, description="Contact detail(s) for the contact person."
    )
    address_use: str | None = Field(None, description="Address purpose.")
    address_type: str | None = Field(None, description="Address type.")
    address_text: str | None = Field(None, description="Full text address.")
    address_line: list[str] | None = Field(None, description="Street address line(s).")
    address_city: str | None = Field(None, description="City.")
    address_district: str | None = Field(None, description="District.")
    address_state: str | None = Field(None, description="State.")
    address_postal_code: str | None = Field(None, description="Postal code.")
    address_country: str | None = Field(None, description="Country.")
    address_period_start: str | None = Field(None, description="Start of address period.")
    address_period_end: str | None = Field(None, description="End of address period.")
    period_start: str | None = Field(None, description="Start of contact validity period.")
    period_end: str | None = Field(None, description="End of contact validity period.")
    organization: str | None = Field(
        None, description="Resolved reference to organization (e.g. 'Organization/190001')."
    )
    organization_type: str | None = Field(None, description="Always 'Organization'.")
    organization_id: int | None = Field(None, description="Public organization_id.")
    organization_display: str | None = Field(None, description="Display text for organization.")
    organization_identifier_system: str | None = Field(None, description="Fallback identifier system.")
    organization_identifier_value: str | None = Field(None, description="Fallback identifier value.")
    organization_identifier_use: str | None = Field(None, description="Fallback identifier use.")
    organization_identifier_type_text: str | None = Field(None, description="Fallback identifier type text.")
