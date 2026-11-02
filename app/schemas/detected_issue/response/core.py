from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)

from .codeable_concept import PlainDetectedIssueCodeableConcept
from .evidence import PlainDetectedIssueEvidence
from .identifier import PlainDetectedIssueIdentifier
from .mitigation import PlainDetectedIssueMitigation
from .reference import PlainDetectedIssueReference


class FHIRDetectedIssueEvidence(BaseModel):
    """DetectedIssue.evidence FHIR element."""

    model_config = ConfigDict(extra="forbid")

    code: list[FHIRCodeableConcept] | None = Field(
        None, description="Manifestation of the issue."
    )
    detail: list[FHIRReference] | None = Field(
        None, description="Supporting information / problem resource."
    )


class FHIRDetectedIssueMitigation(BaseModel):
    """DetectedIssue.mitigation FHIR element."""

    model_config = ConfigDict(extra="forbid")

    action: FHIRCodeableConcept = Field(
        ..., description="What mitigation was taken."
    )
    date: str | None = Field(None, description="Date committed.")
    author: FHIRReference | None = Field(
        None, description="Who committed the mitigation."
    )


class FHIRDetectedIssueSchema(BaseModel):
    """FHIR R4 DetectedIssue resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["DetectedIssue"] = "DetectedIssue"
    id: str = Field(..., description="Logical id of this artifact.")
    meta: FHIRMeta | None = Field(None, description="Metadata about the resource.")
    extension: list[dict[str, Any]] | None = Field(
        None, description="Additional content defined by implementations."
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Business identifier for issue."
    )
    status: str = Field(
        ...,
        description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown",
    )
    code: FHIRCodeableConcept | None = Field(
        None, description="Issue Category, e.g. drug-drug, contraindication."
    )
    severity: str | None = Field(
        None, description="high | moderate | low"
    )
    patient: FHIRReference | None = Field(
        None, description="Associated patient."
    )
    identifiedDateTime: str | None = Field(
        None, description="When identified (dateTime)."
    )
    identifiedPeriod: FHIRPeriod | None = Field(
        None, description="When identified (Period)."
    )
    author: FHIRReference | None = Field(
        None, description="The provider or device that identified the issue."
    )
    implicated: list[FHIRReference] | None = Field(
        None, description="Problem resource."
    )
    evidence: list[FHIRDetectedIssueEvidence] | None = Field(
        None, description="Supporting evidence."
    )
    detail: str | None = Field(
        None, description="Description and context."
    )
    reference: str | None = Field(
        None, description="Authority for issue."
    )
    mitigation: list[FHIRDetectedIssueMitigation] | None = Field(
        None, description="Step taken to address."
    )


class PlainDetectedIssueResponse(BaseModel):
    """Plain snake_case DetectedIssue response schema."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Public sequence identifier.")
    status: str = Field(..., description="Detected issue status.")
    code: PlainDetectedIssueCodeableConcept | None = Field(
        None, description="Issue Category."
    )
    severity: str | None = Field(
        None, description="high | moderate | low."
    )
    patient: PlainDetectedIssueReference | None = Field(
        None, description="Associated patient."
    )
    identified_date_time: datetime | None = Field(
        None, description="When identified (dateTime)."
    )
    identified_period_start: datetime | None = Field(
        None, description="When identified (Period start)."
    )
    identified_period_end: datetime | None = Field(
        None, description="When identified (Period end)."
    )
    author: PlainDetectedIssueReference | None = Field(
        None, description="Provider or device that identified the issue."
    )
    implicated: list[PlainDetectedIssueReference] | None = Field(
        None, description="Problem resource(s)."
    )
    evidence: list[PlainDetectedIssueEvidence] | None = Field(
        None, description="Supporting evidence."
    )
    detail: str | None = Field(
        None, description="Description and context."
    )
    reference: str | None = Field(
        None, description="Authority for issue."
    )
    mitigation: list[PlainDetectedIssueMitigation] | None = Field(
        None, description="Steps taken to address."
    )
    identifier: list[PlainDetectedIssueIdentifier] | None = Field(
        None, description="Business identifiers."
    )
    extension: dict[str, Any] | None = Field(
        None, description="FHIR DomainResource extensions."
    )


class PaginatedDetectedIssueResponse(BaseModel):
    """Paginated plain snake_case DetectedIssue response."""

    model_config = ConfigDict(extra="forbid")

    total: int = Field(..., description="Total number of matching records.")
    limit: int = Field(..., description="Page size limit.")
    offset: int = Field(..., description="Page offset.")
    data: list[PlainDetectedIssueResponse] = Field(
        ..., description="List of matching DetectedIssue records."
    )


class FHIRDetectedIssueBundleEntry(BaseModel):
    """Entry in a FHIR DetectedIssue searchset Bundle."""

    model_config = ConfigDict(extra="forbid")

    fullUrl: str = Field(..., description="Full URL for the resource.")
    resource: FHIRDetectedIssueSchema = Field(..., description="DetectedIssue resource.")


class FHIRDetectedIssueBundle(BaseModel):
    """FHIR R4 searchset Bundle for DetectedIssue."""

    model_config = ConfigDict(extra="forbid")

    resourceType: Literal["Bundle"] = "Bundle"
    type: Literal["searchset"] = "searchset"
    total: int = Field(..., description="Total number of matches.")
    entry: list[FHIRDetectedIssueBundleEntry] = Field(
        default_factory=list, description="Matched resources."
    )
