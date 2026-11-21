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


class FHIRFamilyMemberHistoryAnnotation(BaseModel):
    authorReference: FHIRReference | None = Field(
        None, description="Individual responsible for the annotation."
    )
    authorString: str | None = Field(
        None, description="Individual responsible for the annotation, as plain text."
    )
    time: str | None = Field(None, description="When the annotation was made.")
    text: str | None = Field(None, description="The annotation text.")


class FHIRFamilyMemberHistoryCondition(BaseModel):
    code: FHIRCodeableConcept | None = Field(
        None, description="Condition suffered by relation."
    )
    outcome: FHIRCodeableConcept | None = Field(
        None, description="Result of the condition for the family member."
    )
    contributedToDeath: bool | None = Field(
        None, description="Whether the condition contributed to the cause of death."
    )
    onsetAge: FHIRQuantity | None = Field(
        None, description="When the condition first manifested (Age)."
    )
    onsetRange: FHIRRange | None = Field(
        None, description="When the condition first manifested (Range)."
    )
    onsetPeriod: FHIRPeriod | None = Field(
        None, description="When the condition first manifested (Period)."
    )
    onsetString: str | None = Field(
        None, description="When the condition first manifested (string)."
    )
    note: list[FHIRFamilyMemberHistoryAnnotation] | None = Field(
        None, description="Extra information about condition."
    )


class FHIRFamilyMemberHistorySchema(BaseModel):
    resourceType: str = Field(
        "FamilyMemberHistory", description="Always 'FamilyMemberHistory'."
    )
    id: str = Field(..., description="Public family_member_history_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External Id(s) for this record."
    )
    instantiatesCanonical: list[str] | None = Field(
        None, description="Instantiates FHIR protocol or definition."
    )
    instantiatesUri: list[str] | None = Field(
        None, description="Instantiates external protocol or definition."
    )
    status: str | None = Field(
        None, description="partial | completed | entered-in-error | health-unknown."
    )
    dataAbsentReason: FHIRCodeableConcept | None = Field(
        None, description="subject-unknown | withheld | unable-to-obtain | deferred."
    )
    patient: FHIRReference | None = Field(None, description="Patient history is about.")
    date: str | None = Field(
        None, description="When history was recorded or last updated."
    )
    name: str | None = Field(None, description="The family member described.")
    relationship: FHIRCodeableConcept | None = Field(
        None, description="Relationship to the subject."
    )
    sex: FHIRCodeableConcept | None = Field(
        None, description="male | female | other | unknown."
    )
    bornPeriod: FHIRPeriod | None = Field(
        None, description="(Approximate) date of birth (Period)."
    )
    bornDate: str | None = Field(
        None, description="(Approximate) date of birth (date)."
    )
    bornString: str | None = Field(
        None, description="(Approximate) date of birth (string)."
    )
    ageAge: FHIRQuantity | None = Field(None, description="(Approximate) age (Age).")
    ageRange: FHIRRange | None = Field(None, description="(Approximate) age (Range).")
    ageString: str | None = Field(None, description="(Approximate) age (string).")
    estimatedAge: bool | None = Field(None, description="Age is estimated?")
    deceasedBoolean: bool | None = Field(None, description="Dead? (boolean).")
    deceasedAge: FHIRQuantity | None = Field(
        None, description="Dead? How old/when? (Age)."
    )
    deceasedRange: FHIRRange | None = Field(
        None, description="Dead? How old/when? (Range)."
    )
    deceasedDate: str | None = Field(None, description="Dead? How old/when? (date).")
    deceasedString: str | None = Field(
        None, description="Dead? How old/when? (string)."
    )
    reasonCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Why was family member history performed?"
    )
    reasonReference: list[FHIRReference] | None = Field(
        None, description="Why was family member history performed?"
    )
    note: list[FHIRFamilyMemberHistoryAnnotation] | None = Field(
        None, description="General note about related person."
    )
    condition: list[FHIRFamilyMemberHistoryCondition] | None = Field(
        None, description="Condition that the related person had."
    )


class FHIRFamilyMemberHistoryBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRFamilyMemberHistorySchema | dict = Field(
        ...,
        description="A FamilyMemberHistory (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRFamilyMemberHistoryBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRFamilyMemberHistoryBundleEntry] | None = None
