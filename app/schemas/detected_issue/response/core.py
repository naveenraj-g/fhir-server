from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRDetectedIssueEvidence(BaseModel):
    code: list[FHIRCodeableConcept] | None = Field(None, description="Manifestation.")
    detail: list[FHIRReference] | None = Field(None, description="Supporting information.")


class FHIRDetectedIssueMitigation(BaseModel):
    action: FHIRCodeableConcept | None = Field(None, description="What mitigation?")
    date: str | None = Field(None, description="Date committed.")
    author: FHIRReference | None = Field(None, description="Who is committing?")


class FHIRDetectedIssueSchema(BaseModel):
    resourceType: str = Field("DetectedIssue", description="Always 'DetectedIssue'.")
    id: str = Field(..., description="Public detected_issue_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries."
    )
    identifier: list[FHIRIdentifier] | None = Field(None, description="Unique id for the detected issue.")
    status: str | None = Field(None, description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown.")
    code: FHIRCodeableConcept | None = Field(None, description="Issue category, e.g. drug-drug, duplicate therapy.")
    severity: str | None = Field(None, description="high | moderate | low.")
    patient: FHIRReference | None = Field(None, description="Associated patient.")
    identifiedDateTime: str | None = Field(None, description="When identified (dateTime).")
    identifiedPeriod: FHIRPeriod | None = Field(None, description="When identified (Period).")
    author: FHIRReference | None = Field(None, description="The provider or device that identified the issue.")
    implicated: list[FHIRReference] | None = Field(None, description="Problem resource.")
    evidence: list[FHIRDetectedIssueEvidence] | None = Field(None, description="Supporting evidence.")
    detail: str | None = Field(None, description="Description and context.")
    reference: str | None = Field(None, description="Authority for the issue.")
    mitigation: list[FHIRDetectedIssueMitigation] | None = Field(None, description="Step taken to address.")


class FHIRDetectedIssueBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRDetectedIssueSchema | dict = Field(
        ...,
        description="A DetectedIssue (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Practitioner / PractitionerRole / implicated resource (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRDetectedIssueBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRDetectedIssueBundleEntry] | None = None
