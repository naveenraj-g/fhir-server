from pydantic import BaseModel, Field

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
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink

from .communication import FHIRPatientCommunication
from .contact import FHIRPatientContact
from .link import FHIRPatientLink


class FHIRPatientSchema(BaseModel):
    resourceType: str = Field("Patient", description="Always 'Patient'.")
    id: str = Field(..., description="Public patient_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
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
    gender: str | None = Field(None, description="male | female | other | unknown.")
    birthDate: str | None = Field(
        None, description="The date of birth for the individual."
    )
    deceasedBoolean: bool | None = Field(
        None, description="Indicates if the individual is deceased or not."
    )
    deceasedDateTime: str | None = Field(None, description="Date and time of death.")
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
        None, description="Birth order of a multiple birth."
    )
    photo: list[FHIRAttachment] | None = Field(
        None, description="Image of the patient."
    )
    contact: list[FHIRPatientContact] | None = Field(
        None, description="A contact party for the patient."
    )
    communication: list[FHIRPatientCommunication] | None = Field(
        None,
        description="A language which may be used to communicate with the patient.",
    )
    generalPractitioner: list[FHIRReference] | None = Field(
        None, description="Patient's nominated primary care provider."
    )
    managingOrganization: FHIRReference | None = Field(
        None, description="Organization that is the custodian of the patient record."
    )
    link: list[FHIRPatientLink] | None = Field(
        None,
        description="Link to another patient resource that concerns the same actual person.",
    )


class FHIRPatientBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRPatientSchema | dict = Field(
        ...,
        description="A Patient (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Practitioner / PractitionerRole / Organization / Patient (from _include), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRPatientBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRPatientBundleEntry] | None = None
