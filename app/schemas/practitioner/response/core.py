from pydantic import BaseModel, Field

from app.schemas.common.fhir import (
    FHIRAddress,
    FHIRBundle,
    FHIRContactPoint,
    FHIRHumanName,
    FHIRIdentifier,
)

from .address import PlainPractitionerAddress
from .communication import FHIRCommunication, PlainPractitionerCommunication
from .identifier import PlainPractitionerIdentifier
from .name import PlainPractitionerName
from .photo import FHIRAttachment, PlainPractitionerPhoto
from .qualification import FHIRQualification, PlainQualification
from .telecom import PlainPractitionerTelecom

# ── FHIR (camelCase) ───────────────────────────────────────────────────────────


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
