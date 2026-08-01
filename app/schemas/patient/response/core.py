from pydantic import BaseModel, Field

from app.schemas.common.fhir import (
    FHIRAddress,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRHumanName,
    FHIRIdentifier,
    FHIRReference,
)

from .address import PlainPatientAddress
from .communication import FHIRPatientCommunication, PlainPatientCommunication
from .contact import FHIRPatientContact, PlainPatientContact
from .general_practitioner import PlainPatientGeneralPractitioner
from .identifier import PlainPatientIdentifier
from .link import FHIRPatientLink, PlainPatientLink
from .name import PlainPatientName
from .photo import FHIRAttachment, PlainPatientPhoto
from .telecom import PlainPatientTelecom

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
        None,
        description="Fallback identifier — ISO 8601 datetime it stopped being valid.",
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
        None,
        description="Fallback identifier — ISO 8601 datetime it stopped being valid.",
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
