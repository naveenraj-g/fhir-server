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
from app.schemas.datatypes.dosage import FHIRDosage
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRMedicationStatementSchema(BaseModel):
    resourceType: str = Field(
        "MedicationStatement", description="Always 'MedicationStatement'."
    )
    id: str = Field(..., description="Public medication_statement_id as a string.")
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
    basedOn: list[FHIRReference] | None = Field(
        None, description="Fulfils plan, proposal or order."
    )
    partOf: list[FHIRReference] | None = Field(
        None, description="Part of referenced event."
    )
    status: str | None = Field(
        None,
        description="active | completed | entered-in-error | intended | stopped | on-hold | unknown | not-taken.",
    )
    statusReason: list[FHIRCodeableConcept] | None = Field(
        None, description="Reason for current status."
    )
    category: FHIRCodeableConcept | None = Field(
        None, description="Type of medication usage."
    )
    medicationCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="What medication was taken (a CodeableConcept)."
    )
    medicationReference: FHIRReference | None = Field(
        None, description="What medication was taken (a Reference(Medication))."
    )
    subject: FHIRReference | None = Field(
        None, description="Who is/was taking the medication."
    )
    context: FHIRReference | None = Field(
        None, description="Encounter / Episode associated with MedicationStatement."
    )
    effectiveDateTime: str | None = Field(
        None, description="When the medication is/was/will be taken (a dateTime)."
    )
    effectivePeriod: FHIRPeriod | None = Field(
        None, description="The interval when the medication is/was/will be taken."
    )
    dateAsserted: str | None = Field(
        None, description="When the statement was asserted."
    )
    informationSource: FHIRReference | None = Field(
        None, description="Person or organization that provided the information."
    )
    derivedFrom: list[FHIRReference] | None = Field(
        None, description="Additional supporting information."
    )
    reasonCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Reason for why the medication is being/was taken."
    )
    reasonReference: list[FHIRReference] | None = Field(
        None, description="Condition or observation that supports the use."
    )
    note: list[FHIRAnnotation] | None = Field(
        None, description="Further information about the statement."
    )
    dosage: list[FHIRDosage] | None = Field(
        None, description="Details of how the medication is/was taken."
    )


class FHIRMedicationStatementBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRMedicationStatementSchema | dict = Field(
        ...,
        description="A MedicationStatement (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Group / Encounter / EpisodeOfCare / Practitioner / PractitionerRole / RelatedPerson / Organization / Medication / Observation / Procedure / MedicationStatement (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRMedicationStatementBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRMedicationStatementBundleEntry] | None = None
