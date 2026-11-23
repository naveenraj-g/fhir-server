from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.datatypes.annotation import FHIRAnnotation
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRMedicationAdministrationPerformer(BaseModel):
    function: FHIRCodeableConcept | None = Field(
        None, description="Type of performance."
    )
    actor: FHIRReference | None = Field(
        None, description="Who performed the administration."
    )


class FHIRMedicationAdministrationSchema(BaseModel):
    resourceType: str = Field(
        "MedicationAdministration", description="Always 'MedicationAdministration'."
    )
    id: str = Field(..., description="Public medication_administration_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External identifier."
    )
    instantiates: list[str] | None = Field(
        None, description="Instantiates protocol or definition."
    )
    partOf: list[FHIRReference] | None = Field(
        None, description="Part of referenced event."
    )
    status: str | None = Field(
        None,
        description="in-progress | not-done | on-hold | completed | entered-in-error | stopped | unknown.",
    )
    statusReason: list[FHIRCodeableConcept] | None = Field(
        None, description="Reason administration not performed."
    )
    category: FHIRCodeableConcept | None = Field(
        None, description="Type of medication usage."
    )
    medicationCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="What was administered (a CodeableConcept)."
    )
    medicationReference: FHIRReference | None = Field(
        None, description="What was administered (a Reference(Medication))."
    )
    subject: FHIRReference | None = Field(
        None, description="Who received the medication."
    )
    context: FHIRReference | None = Field(
        None, description="Encounter or Episode of Care administered as part of."
    )
    supportingInformation: list[FHIRReference] | None = Field(
        None, description="Additional information to support administration."
    )
    effectiveDateTime: str | None = Field(
        None, description="Start and end time of administration (a dateTime)."
    )
    effectivePeriod: FHIRPeriod | None = Field(
        None, description="Start and end time of administration (a Period)."
    )
    performer: list[FHIRMedicationAdministrationPerformer] | None = Field(
        None, description="Who performed the medication administration."
    )
    reasonCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Reason administration performed."
    )
    reasonReference: list[FHIRReference] | None = Field(
        None, description="Condition or observation that supports the administration."
    )
    request: FHIRReference | None = Field(
        None, description="Request administration performed against."
    )
    device: list[FHIRReference] | None = Field(
        None, description="Device used to administer."
    )
    note: list[FHIRAnnotation] | None = Field(
        None, description="Information about the administration."
    )
    dosage: dict | None = Field(
        None, description="Details of how medication was taken."
    )
    eventHistory: list[FHIRReference] | None = Field(
        None, description="A list of events of interest in the lifecycle."
    )


class FHIRMedicationAdministrationBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRMedicationAdministrationSchema | dict = Field(
        ...,
        description="A MedicationAdministration (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Group / Encounter / EpisodeOfCare / Practitioner / PractitionerRole / RelatedPerson / Medication / MedicationRequest (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRMedicationAdministrationBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRMedicationAdministrationBundleEntry] | None = None
