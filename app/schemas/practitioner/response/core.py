from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRAddress,
    FHIRAttachment,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRHumanName,
    FHIRIdentifier,
    FHIRMeta,
)

from .address import PlainPractitionerAddress
from .communication import PlainPractitionerCommunication
from .identifier import PlainPractitionerIdentifier
from .name import PlainPractitionerName
from .photo import PlainPractitionerPhoto
from .qualification import FHIRPractitionerQualification, PlainPractitionerQualification
from .telecom import PlainPractitionerTelecom

# ── FHIR (camelCase) ─────────────────────────────────────────────────────


class FHIRPractitionerSchema(BaseModel):
    resourceType: str = Field("Practitioner", description="Always 'Practitioner'.")
    id: str = Field(..., description="Public practitioner_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries. Not yet validated against registered extension definitions.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Identifiers for the person in this role."
    )
    active: bool | None = Field(
        None, description="Whether this practitioner's record is in active use."
    )
    name: list[FHIRHumanName] | None = Field(
        None, description="Name(s) associated with the practitioner."
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None, description="Contact details applying to all roles."
    )
    address: list[FHIRAddress] | None = Field(
        None, description="Non-role-specific addresses, typically home."
    )
    gender: str | None = Field(None, description="male|female|other|unknown.")
    birthDate: str | None = Field(None, description="Date of birth.")
    photo: list[FHIRAttachment] | None = Field(
        None, description="Image(s) of the person."
    )
    qualification: list[FHIRPractitionerQualification] | None = Field(
        None, description="Certifications, licenses, or training."
    )
    communication: list[FHIRCodeableConcept] | None = Field(
        None, description="Languages the practitioner can use in patient communication."
    )


class FHIRPractitionerBundleEntry(BaseModel):
    resource: FHIRPractitionerSchema


class FHIRPractitionerBundle(FHIRBundle):
    entry: list[FHIRPractitionerBundleEntry] | None = None


# ── Plain (snake_case) ────────────────────────────────────────────────────


class PlainPractitionerResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public practitioner_id.")
    user_id: str | None = Field(
        None, description="Gateway-forwarded acting end-user's own account ID."
    )
    active: bool | None = Field(
        None, description="Whether this practitioner's record is in active use."
    )
    gender: str | None = Field(None, description="male|female|other|unknown.")
    birth_date: str | None = Field(None, description="Date of birth.")
    identifier: list[PlainPractitionerIdentifier] | None = Field(
        None, description="Identifiers for the person in this role."
    )
    name: list[PlainPractitionerName] | None = Field(
        None, description="Name(s) associated with the practitioner."
    )
    telecom: list[PlainPractitionerTelecom] | None = Field(
        None, description="Contact details applying to all roles."
    )
    address: list[PlainPractitionerAddress] | None = Field(
        None, description="Non-role-specific addresses, typically home."
    )
    photo: list[PlainPractitionerPhoto] | None = Field(
        None, description="Image(s) of the person."
    )
    qualification: list[PlainPractitionerQualification] | None = Field(
        None, description="Certifications, licenses, or training."
    )
    communication: list[PlainPractitionerCommunication] | None = Field(
        None, description="Languages the practitioner can use in patient communication."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries.",
    )
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded ID of the tenant/account this record is scoped to (multi-tenancy) — not a FHIR concept. Internally this column is named tenant_id (see app/models/shared/tenant_audit.py) to avoid ambiguity with the Organization entity itself; the external field name stays org_id for consistency with every other resource's response contract.",
    )
    created_at: str | None = Field(None, description="When this row was created.")
    updated_at: str | None = Field(None, description="When this row was last updated.")
    created_by: str | None = Field(
        None, description="Acting user who created this record, taken from the verified JWT's sub."
    )
    updated_by: str | None = Field(
        None,
        description="Acting user who last updated this record, taken from the verified JWT's sub.",
    )


class PaginatedPractitionerResponse(BaseModel):
    total: int | None = Field(
        None, description="Total matching rows (null when total_mode=none)."
    )
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Number of rows skipped before this page.")
    data: list[PlainPractitionerResponse]
