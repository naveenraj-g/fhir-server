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


class FHIRConditionAnnotation(BaseModel):
    authorReference: FHIRReference | None = Field(None, description="Individual responsible for the annotation.")
    authorString: str | None = Field(None, description="Individual responsible for the annotation, as plain text.")
    time: str | None = Field(None, description="When the annotation was made.")
    text: str | None = Field(None, description="The annotation text.")


class FHIRConditionStage(BaseModel):
    summary: FHIRCodeableConcept | None = Field(None, description="Simple summary (disease specific).")
    assessment: list[FHIRReference] | None = Field(None, description="Formal record of assessment.")
    type: FHIRCodeableConcept | None = Field(None, description="Kind of staging, such as pathological or clinical staging.")


class FHIRConditionEvidence(BaseModel):
    code: list[FHIRCodeableConcept] | None = Field(None, description="Manifestation/symptom.")
    detail: list[FHIRReference] | None = Field(None, description="Supporting information found elsewhere.")


class FHIRConditionSchema(BaseModel):
    resourceType: str = Field("Condition", description="Always 'Condition'.")
    id: str = Field(..., description="Public condition_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries."
    )
    identifier: list[FHIRIdentifier] | None = Field(None, description="External Ids for this condition.")
    clinicalStatus: FHIRCodeableConcept | None = Field(None, description="active | recurrence | relapse | inactive | remission | resolved.")
    verificationStatus: FHIRCodeableConcept | None = Field(None, description="unconfirmed | provisional | differential | confirmed | refuted | entered-in-error.")
    category: list[FHIRCodeableConcept] | None = Field(None, description="problem-list-item | encounter-diagnosis.")
    severity: FHIRCodeableConcept | None = Field(None, description="Subjective severity of condition.")
    code: FHIRCodeableConcept | None = Field(None, description="Identification of the condition, problem or diagnosis.")
    bodySite: list[FHIRCodeableConcept] | None = Field(None, description="Anatomical location, if relevant.")
    subject: FHIRReference | None = Field(None, description="Who has the condition.")
    encounter: FHIRReference | None = Field(None, description="Encounter created as part of.")
    onsetDateTime: str | None = Field(None, description="Estimated or actual date, date-time, or age.")
    onsetAge: FHIRQuantity | None = Field(None, description="Estimated or actual age (Age).")
    onsetPeriod: FHIRPeriod | None = Field(None, description="Estimated or actual period (Period).")
    onsetRange: FHIRRange | None = Field(None, description="Estimated or actual age range (Range).")
    onsetString: str | None = Field(None, description="Estimated or actual onset as text.")
    abatementDateTime: str | None = Field(None, description="When in resolution/remission.")
    abatementAge: FHIRQuantity | None = Field(None, description="When in resolution/remission (Age).")
    abatementPeriod: FHIRPeriod | None = Field(None, description="When in resolution/remission (Period).")
    abatementRange: FHIRRange | None = Field(None, description="When in resolution/remission (Range).")
    abatementString: str | None = Field(None, description="When in resolution/remission, as text.")
    recordedDate: str | None = Field(None, description="Date record was first recorded.")
    recorder: FHIRReference | None = Field(None, description="Who recorded the condition.")
    asserter: FHIRReference | None = Field(None, description="Person who asserts this condition.")
    stage: list[FHIRConditionStage] | None = Field(None, description="Stage/grade, usually assessed formally.")
    evidence: list[FHIRConditionEvidence] | None = Field(None, description="Supporting evidence.")
    note: list[FHIRConditionAnnotation] | None = Field(None, description="Additional information about the Condition.")


class FHIRConditionBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRConditionSchema | dict = Field(
        ...,
        description="A Condition (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Practitioner / PractitionerRole / RelatedPerson / Encounter (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRConditionBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRConditionBundleEntry] | None = None
