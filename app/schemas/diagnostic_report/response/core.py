from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRAttachment,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRDiagnosticReportMedia(BaseModel):
    comment: str | None = Field(
        None, description="Comment about the image (e.g. explanation)."
    )
    link: FHIRReference | None = Field(
        None, description="Reference to the image source."
    )


class FHIRDiagnosticReportSchema(BaseModel):
    resourceType: str = Field(
        "DiagnosticReport", description="Always 'DiagnosticReport'."
    )
    id: str = Field(..., description="Public diagnostic_report_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Business identifier for report."
    )
    basedOn: list[FHIRReference] | None = Field(None, description="What was requested.")
    status: str | None = Field(
        None,
        description="registered | partial | preliminary | final | amended | corrected | appended | cancelled | entered-in-error | unknown.",
    )
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="Service category."
    )
    code: FHIRCodeableConcept | None = Field(
        None, description="Name/Code for this diagnostic report."
    )
    subject: FHIRReference | None = Field(
        None, description="The subject of the report."
    )
    encounter: FHIRReference | None = Field(
        None, description="Health care event when test ordered."
    )
    effectiveDateTime: str | None = Field(
        None, description="Clinically relevant time/time-period for report."
    )
    effectivePeriod: FHIRPeriod | None = Field(
        None, description="Clinically relevant time/time-period for report (Period)."
    )
    issued: str | None = Field(None, description="DateTime this version was made.")
    performer: list[FHIRReference] | None = Field(
        None, description="Responsible Diagnostic Service."
    )
    resultsInterpreter: list[FHIRReference] | None = Field(
        None, description="Primary result interpreter."
    )
    specimen: list[FHIRReference] | None = Field(
        None, description="Specimens this report is based on."
    )
    result: list[FHIRReference] | None = Field(None, description="Observations.")
    imagingStudy: list[FHIRReference] | None = Field(
        None,
        description="Reference to full details of imaging associated with the diagnostic report.",
    )
    media: list[FHIRDiagnosticReportMedia] | None = Field(
        None, description="Key images associated with this report."
    )
    conclusion: str | None = Field(
        None, description="Clinical conclusion (interpretation) of test results."
    )
    conclusionCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Codes for the clinical conclusion of test results."
    )
    presentedForm: list[FHIRAttachment] | None = Field(
        None, description="Entire report as issued."
    )


class FHIRDiagnosticReportBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRDiagnosticReportSchema | dict = Field(
        ...,
        description="A DiagnosticReport (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Location / Encounter / Practitioner / PractitionerRole / Organization (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRDiagnosticReportBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRDiagnosticReportBundleEntry] | None = None
