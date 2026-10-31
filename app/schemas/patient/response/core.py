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
    FHIRReference,
    PlainCodingRow,
)

from .address import PlainPatientAddress
from .communication import FHIRPatientCommunication, PlainPatientCommunication
from .contact import FHIRPatientContact, PlainPatientContact
from .general_practitioner import PlainPatientGeneralPractitioner
from .identifier import PlainPatientIdentifier
from .link import FHIRPatientLink, PlainPatientLink
from .name import PlainPatientName
from .photo import PlainPatientPhoto
from .telecom import PlainPatientTelecom

# ── FHIR (camelCase) ─────────────────────────────────────────────────────


class FHIRPatientSchema(BaseModel):
    resourceType: str = Field("Patient", description="Always 'Patient'.")
    id: str = Field(..., description="Public patient_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="An identifier for this patient."
    )
    active: bool | None = Field(
        None, description="Whether this patient's record is in active use."
    )
    name: list[FHIRHumanName] | None = Field(
        None, description="A name associated with the patient."
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None, description="A contact detail for the individual."
    )
    gender: str | None = Field(
        None, description="male | female | other | unknown."
    )
    birthDate: str | None = Field(None, description="The date of birth for the individual.")
    deceasedBoolean: bool | None = Field(
        None, description="Indicates if the individual is deceased or not."
    )
    deceasedDateTime: str | None = Field(
        None, description="The date and time when the individual died."
    )
    address: list[FHIRAddress] | None = Field(
        None, description="An address for the individual."
    )
    maritalStatus: FHIRCodeableConcept | None = Field(
        None, description="Marital (civil) status of a patient."
    )
    multipleBirthBoolean: bool | None = Field(
        None, description="Whether patient is part of a multiple birth."
    )
    multipleBirthInteger: int | None = Field(
        None, description="Birth order in a multiple birth."
    )
    photo: list[FHIRAttachment] | None = Field(
        None, description="Image of the patient."
    )
    contact: list[FHIRPatientContact] | None = Field(
        None, description="A contact party for the patient."
    )
    communication: list[FHIRPatientCommunication] | None = Field(
        None, description="A language which may be used to communicate with the patient."
    )
    generalPractitioner: list[FHIRReference] | None = Field(
        None, description="Patient's nominated primary care provider."
    )
    managingOrganization: FHIRReference | None = Field(
        None, description="Organization that is the custodian of the patient record."
    )
    link: list[FHIRPatientLink] | None = Field(
        None, description="Link to a Patient or RelatedPerson resource that concerns the same actual individual."
    )


class FHIRPatientBundleEntry(BaseModel):
    resource: FHIRPatientSchema


class FHIRPatientBundle(FHIRBundle):
    entry: list[FHIRPatientBundleEntry] | None = None


# ── Plain (snake_case) ────────────────────────────────────────────────────


class PlainPatientResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public patient_id.")
    user_id: str | None = Field(
        None, description="Gateway-forwarded acting end-user's own account ID."
    )
    active: bool | None = Field(
        None, description="Whether this patient's record is in active use."
    )
    gender: str | None = Field(
        None, description="Administrative Gender — male|female|other|unknown."
    )
    birth_date: str | None = Field(None, description="Date of birth.")
    deceased_boolean: bool | None = Field(None, description="Indicates if deceased.")
    deceased_date_time: str | None = Field(None, description="Date/time of death.")
    marital_status_text: str | None = Field(None, description="Marital status text.")
    marital_status_codings: list[PlainCodingRow] | None = Field(
        None, description="Marital status coding(s)."
    )
    multiple_birth_boolean: bool | None = Field(None, description="Part of multiple birth.")
    multiple_birth_integer: int | None = Field(None, description="Multiple birth order.")
    managing_organization_reference: str | None = Field(
        None, description="Raw managing organization reference string as received."
    )
    managing_organization: str | None = Field(
        None, description="Resolved managing organization reference (e.g. 'Organization/190001')."
    )
    managing_organization_type: str | None = Field(None, description="Always 'Organization'.")
    managing_organization_id: int | None = Field(None, description="Public organization_id.")
    managing_organization_display: str | None = Field(None, description="Managing organization display text.")
    managing_organization_identifier_system: str | None = Field(None, description="Fallback identifier system.")
    managing_organization_identifier_value: str | None = Field(None, description="Fallback identifier value.")
    managing_organization_identifier_use: str | None = Field(None, description="Fallback identifier use.")
    managing_organization_identifier_type_text: str | None = Field(None, description="Fallback identifier type text.")

    identifier: list[PlainPatientIdentifier] | None = Field(
        None, description="An identifier for this patient."
    )
    name: list[PlainPatientName] | None = Field(
        None, description="A name associated with the patient."
    )
    telecom: list[PlainPatientTelecom] | None = Field(
        None, description="A contact detail for the individual."
    )
    address: list[PlainPatientAddress] | None = Field(
        None, description="An address for the individual."
    )
    photo: list[PlainPatientPhoto] | None = Field(
        None, description="Image of the patient."
    )
    contact: list[PlainPatientContact] | None = Field(
        None, description="A contact party for the patient."
    )
    communication: list[PlainPatientCommunication] | None = Field(
        None, description="Languages for patient communication."
    )
    general_practitioner: list[PlainPatientGeneralPractitioner] | None = Field(
        None, description="Nominated care providers."
    )
    link: list[PlainPatientLink] | None = Field(
        None, description="Links to other resources."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries.",
    )
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded ID of the tenant/account this record is scoped to (multi-tenancy).",
    )
    created_at: str | None = Field(None, description="When this row was created.")
    updated_at: str | None = Field(None, description="When this row was last updated.")
    created_by: str | None = Field(
        None, description="Acting user who created this record, from verified JWT sub."
    )
    updated_by: str | None = Field(
        None, description="Acting user who last updated this record, from verified JWT sub."
    )


class PaginatedPatientResponse(BaseModel):
    total: int | None = Field(
        None, description="Total matching rows (null when total_mode=none)."
    )
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Number of rows skipped before this page.")
    data: list[PlainPatientResponse]
