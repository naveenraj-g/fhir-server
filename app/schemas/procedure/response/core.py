from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRQuantity,
    FHIRRange,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRProcedureAnnotation(BaseModel):
    authorReference: FHIRReference | None = Field(None, description="Individual responsible for the annotation.")
    authorString: str | None = Field(None, description="Individual responsible for the annotation, as plain text.")
    time: str | None = Field(None, description="When the annotation was made.")
    text: str | None = Field(None, description="The annotation text.")


class FHIRProcedurePerformer(BaseModel):
    function: FHIRCodeableConcept | None = Field(None, description="Type of performance.")
    actor: FHIRReference | None = Field(None, description="Who performed the procedure.")
    onBehalfOf: FHIRReference | None = Field(None, description="Organization the device or practitioner was acting for.")


class FHIRProcedureFocalDevice(BaseModel):
    action: FHIRCodeableConcept | None = Field(None, description="Kind of change to device.")
    manipulated: FHIRReference | None = Field(None, description="Device that was changed.")


class FHIRProcedureSchema(BaseModel):
    resourceType: str = Field("Procedure", description="Always 'Procedure'.")
    id: str = Field(..., description="Public procedure_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries."
    )
    identifier: list[FHIRIdentifier] | None = Field(None, description="External Identifiers for this procedure.")
    instantiatesCanonical: list[str] | None = Field(None, description="Instantiates FHIR protocol or definition.")
    instantiatesUri: list[str] | None = Field(None, description="Instantiates external protocol or definition.")
    basedOn: list[FHIRReference] | None = Field(None, description="A request for this procedure.")
    partOf: list[FHIRReference] | None = Field(None, description="Part of referenced event.")
    status: str | None = Field(None, description="preparation | in-progress | not-done | on-hold | stopped | completed | entered-in-error | unknown.")
    statusReason: FHIRCodeableConcept | None = Field(None, description="Reason for current status.")
    category: FHIRCodeableConcept | None = Field(None, description="Classification of the procedure.")
    code: FHIRCodeableConcept | None = Field(None, description="Identification of the procedure.")
    subject: FHIRReference | None = Field(None, description="Who the procedure was performed on.")
    encounter: FHIRReference | None = Field(None, description="Encounter created as part of.")
    performedDateTime: str | None = Field(None, description="When the procedure was performed.")
    performedPeriod: FHIRPeriod | None = Field(None, description="When the procedure was performed (Period).")
    performedString: str | None = Field(None, description="When the procedure was performed, as text.")
    performedAge: FHIRQuantity | None = Field(None, description="When the procedure was performed (Age).")
    performedRange: FHIRRange | None = Field(None, description="When the procedure was performed (Range).")
    recorder: FHIRReference | None = Field(None, description="Who recorded the procedure.")
    asserter: FHIRReference | None = Field(None, description="Person who asserts this procedure.")
    performer: list[FHIRProcedurePerformer] | None = Field(None, description="The people who performed the procedure.")
    location: FHIRReference | None = Field(None, description="Where the procedure happened.")
    reasonCode: list[FHIRCodeableConcept] | None = Field(None, description="Coded reason procedure performed.")
    reasonReference: list[FHIRReference] | None = Field(None, description="The justification that the procedure was performed.")
    bodySite: list[FHIRCodeableConcept] | None = Field(None, description="Target body sites.")
    outcome: FHIRCodeableConcept | None = Field(None, description="The result of procedure.")
    report: list[FHIRReference] | None = Field(None, description="Any report resulting from the procedure.")
    complication: list[FHIRCodeableConcept] | None = Field(None, description="Complication following the procedure.")
    complicationDetail: list[FHIRReference] | None = Field(None, description="A condition that is a result of the procedure.")
    followUp: list[FHIRCodeableConcept] | None = Field(None, description="Instructions for follow up.")
    note: list[FHIRProcedureAnnotation] | None = Field(None, description="Additional information about the procedure.")
    focalDevice: list[FHIRProcedureFocalDevice] | None = Field(None, description="Manipulated, implanted, or removed device.")
    usedReference: list[FHIRReference] | None = Field(None, description="Items used during procedure.")
    usedCode: list[FHIRCodeableConcept] | None = Field(None, description="Coded items used during the procedure.")


class FHIRProcedureBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRProcedureSchema | dict = Field(
        ...,
        description="A Procedure (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Practitioner / PractitionerRole / RelatedPerson / Organization / Encounter / Location / Condition / Procedure (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRProcedureBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRProcedureBundleEntry] | None = None
