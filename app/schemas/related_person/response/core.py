from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    AuditFields,
    FHIRAddress,
    FHIRAttachment,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRHumanName,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)

from .address import PlainRelatedPersonAddress
from .communication import (
    FHIRRelatedPersonCommunication,
    PlainRelatedPersonCommunication,
)
from .identifier import PlainRelatedPersonIdentifier
from .name import PlainRelatedPersonName
from .photo import PlainRelatedPersonPhoto
from .relationship import PlainRelatedPersonRelationship
from .telecom import PlainRelatedPersonTelecom

# ── FHIR (camelCase) ──────────────────────────────────────────────────────────


class FHIRRelatedPersonSchema(BaseModel):
    resourceType: str = Field("RelatedPerson", description="Always 'RelatedPerson'.")
    id: str = Field(..., description="Public related_person_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus org_id/created_by/updated_by/created_at as extensions.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="An identifier for this person."
    )
    active: bool | None = Field(
        None, description="Whether this related person's record is in active use."
    )
    patient: FHIRReference = Field(
        ..., description="The patient this person is related to."
    )
    relationship: list[FHIRCodeableConcept] | None = Field(
        None,
        description="The nature of the relationship between a patient and the related person.",
    )
    name: list[FHIRHumanName] | None = Field(
        None, description="A name associated with the person."
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None, description="A contact detail for the person."
    )
    gender: str | None = Field(
        None, description="male | female | other | unknown."
    )
    birthDate: str | None = Field(
        None, description="The date on which the related person was born."
    )
    address: list[FHIRAddress] | None = Field(
        None, description="Address where the related person can be contacted or visited."
    )
    photo: list[FHIRAttachment] | None = Field(
        None, description="Image of the person."
    )
    period: FHIRPeriod | None = Field(
        None,
        description="Period of time that this relationship is considered valid.",
    )
    communication: list[FHIRRelatedPersonCommunication] | None = Field(
        None,
        description="A language which may be used to communicate with about the patient's health.",
    )


class FHIRRelatedPersonBundleEntry(BaseModel):
    resource: FHIRRelatedPersonSchema


class FHIRRelatedPersonBundle(FHIRBundle):
    entry: list[FHIRRelatedPersonBundleEntry] | None = None


# ── Plain (snake_case) ─────────────────────────────────────────────────────────


class PlainRelatedPersonResponse(AuditFields):
    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Public related_person_id.")
    active: bool | None = Field(
        None, description="Whether this related person's record is in active use."
    )
    patient_reference: str = Field(
        ..., description="Raw literal string of patient reference."
    )
    patient_type: str | None = Field(
        None, description="Target resource type (always 'Patient')."
    )
    patient_id: int | None = Field(
        None, description="Resolved public patient_id."
    )
    patient_display: str | None = Field(
        None, description="Display text for the patient reference."
    )
    gender: str | None = Field(
        None, description="Administrative Gender — male|female|other|unknown."
    )
    birth_date: str | None = Field(
        None, description="The date on which the related person was born (YYYY-MM-DD)."
    )
    period_start: str | None = Field(
        None, description="Start of validity period."
    )
    period_end: str | None = Field(
        None, description="End of validity period."
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions."
    )

    identifiers: list[PlainRelatedPersonIdentifier] | None = Field(
        None, description="Identifiers for this person."
    )
    relationships: list[PlainRelatedPersonRelationship] | None = Field(
        None, description="Relationships to the patient."
    )
    names: list[PlainRelatedPersonName] | None = Field(
        None, description="Names associated with the person."
    )
    telecoms: list[PlainRelatedPersonTelecom] | None = Field(
        None, description="Contact details for the person."
    )
    addresses: list[PlainRelatedPersonAddress] | None = Field(
        None, description="Addresses for the person."
    )
    photos: list[PlainRelatedPersonPhoto] | None = Field(
        None, description="Images of the person."
    )
    communications: list[PlainRelatedPersonCommunication] | None = Field(
        None, description="Languages for communication."
    )


class PaginatedRelatedPersonResponse(BaseModel):
    total: int = Field(..., description="Total matching records.")
    limit: int = Field(..., description="Maximum results returned.")
    offset: int = Field(..., description="Offset applied.")
    data: list[PlainRelatedPersonResponse] = Field(
        ..., description="Page of related person records."
    )
