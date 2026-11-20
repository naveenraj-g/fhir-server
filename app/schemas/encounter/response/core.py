from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRCoding,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRQuantity,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIREncounterStatusHistory(BaseModel):
    status: str | None = Field(None, description="planned | arrived | triaged | in-progress | onleave | finished | cancelled | entered-in-error | unknown.")
    period: FHIRPeriod | None = Field(None, description="The time that the episode was in the specified status.")


class FHIREncounterClassHistory(BaseModel):
    class_: FHIRCoding | None = Field(None, alias="class", description="inpatient | outpatient | ambulatory | emergency +.")
    period: FHIRPeriod | None = Field(None, description="The time that the episode was in the specified class.")


class FHIREncounterParticipant(BaseModel):
    type: list[FHIRCodeableConcept] | None = Field(None, description="Role of participant in encounter.")
    period: FHIRPeriod | None = Field(None, description="Period of time during the encounter that the participant participated.")
    individual: FHIRReference | None = Field(None, description="Persons involved in the encounter other than the patient.")


class FHIREncounterDiagnosis(BaseModel):
    condition: FHIRReference | None = Field(None, description="The diagnosis or procedure relevant to the encounter.")
    use: FHIRCodeableConcept | None = Field(None, description="Role that this diagnosis has within the encounter.")
    rank: int | None = Field(None, description="Ranking of the diagnosis (for each role type).")


class FHIREncounterHospitalization(BaseModel):
    preAdmissionIdentifier: FHIRIdentifier | None = Field(None, description="Pre-admission identifier.")
    origin: FHIRReference | None = Field(None, description="The location/organization from which the patient came before admission.")
    admitSource: FHIRCodeableConcept | None = Field(None, description="From where patient was admitted (physician referral, transfer).")
    reAdmission: FHIRCodeableConcept | None = Field(None, description="The type of hospital re-admission that has occurred (if any).")
    dietPreference: list[FHIRCodeableConcept] | None = Field(None, description="Diet preferences reported by the patient.")
    specialCourtesy: list[FHIRCodeableConcept] | None = Field(None, description="Special courtesies (VIP, board member).")
    specialArrangement: list[FHIRCodeableConcept] | None = Field(None, description="Wheelchair, translator, stretcher, etc.")
    destination: FHIRReference | None = Field(None, description="Location/organization to which the patient is discharged.")
    dischargeDisposition: FHIRCodeableConcept | None = Field(None, description="Category or kind of location after discharge.")


class FHIREncounterLocation(BaseModel):
    location: FHIRReference | None = Field(None, description="Location the encounter takes place.")
    status: str | None = Field(None, description="planned | active | reserved | completed.")
    physicalType: FHIRCodeableConcept | None = Field(None, description="The physical type of the location.")
    period: FHIRPeriod | None = Field(None, description="Time period during which the patient was present at the location.")


class FHIREncounterSchema(BaseModel):
    resourceType: str = Field("Encounter", description="Always 'Encounter'.")
    id: str = Field(..., description="Public encounter_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries."
    )
    identifier: list[FHIRIdentifier] | None = Field(None, description="Identifier(s) by which this encounter is known.")
    status: str | None = Field(None, description="planned | arrived | triaged | in-progress | onleave | finished | cancelled | entered-in-error | unknown.")
    statusHistory: list[FHIREncounterStatusHistory] | None = Field(None, description="List of past encounter statuses.")
    class_: FHIRCoding | None = Field(None, alias="class", description="Classification of patient encounter.")
    classHistory: list[FHIREncounterClassHistory] | None = Field(None, description="List of past encounter classes.")
    type: list[FHIRCodeableConcept] | None = Field(None, description="Specific type of encounter.")
    serviceType: FHIRCodeableConcept | None = Field(None, description="Specific type of service.")
    priority: FHIRCodeableConcept | None = Field(None, description="Indicates the urgency of the encounter.")
    subject: FHIRReference | None = Field(None, description="The patient or group present at the encounter.")
    episodeOfCare: list[FHIRReference] | None = Field(None, description="Episode(s) of care that this encounter should be recorded against.")
    basedOn: list[FHIRReference] | None = Field(None, description="The ServiceRequest that initiated this encounter.")
    participant: list[FHIREncounterParticipant] | None = Field(None, description="List of participants involved in the encounter.")
    appointment: list[FHIRReference] | None = Field(None, description="The appointment that scheduled this encounter.")
    period: FHIRPeriod | None = Field(None, description="The start and end time of the encounter.")
    length: FHIRQuantity | None = Field(None, description="Quantity of time the encounter lasted (less time absent).")
    reasonCode: list[FHIRCodeableConcept] | None = Field(None, description="Coded reason the encounter takes place.")
    reasonReference: list[FHIRReference] | None = Field(None, description="Reason the encounter takes place (reference).")
    diagnosis: list[FHIREncounterDiagnosis] | None = Field(None, description="The list of diagnosis relevant to this encounter.")
    account: list[FHIRReference] | None = Field(None, description="The set of accounts that may be used for billing for this Encounter.")
    hospitalization: FHIREncounterHospitalization | None = Field(None, description="Details about the admission to a healthcare service.")
    location: list[FHIREncounterLocation] | None = Field(None, description="List of locations where the patient has been.")
    serviceProvider: FHIRReference | None = Field(None, description="The organization (facility) responsible for this encounter.")
    partOf: FHIRReference | None = Field(None, description="Another Encounter this encounter is part of.")


class FHIREncounterBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIREncounterSchema | dict = Field(
        ...,
        description="An Encounter (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Appointment / Patient / Practitioner / PractitionerRole / Location / Organization / Encounter (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIREncounterBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIREncounterBundleEntry] | None = None
