from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
    PlainCodingRow,
)

from .codeable_concept import PlainDiagnosticReportCodeableConcept
from .identifier import PlainDiagnosticReportIdentifier
from .media import PlainDiagnosticReportMedia
from .presented_form import PlainDiagnosticReportPresentedForm
from .reference import (
    PlainDiagnosticReportBasedOn,
    PlainDiagnosticReportEncounter,
    PlainDiagnosticReportImagingStudy,
    PlainDiagnosticReportPerformer,
    PlainDiagnosticReportResult,
    PlainDiagnosticReportResultsInterpreter,
    PlainDiagnosticReportSpecimen,
    PlainDiagnosticReportSubject,
)

# ── FHIR (camelCase) ────────────────────────────────────────────────────────


class FHIRDiagnosticReportMedia(BaseModel):
    """DiagnosticReport.media (0..*)."""

    comment: str | None = None
    link: FHIRReference


class FHIRDiagnosticReportAttachment(BaseModel):
    """FHIR R4 Attachment — https://www.hl7.org/fhir/R4/datatypes.html#Attachment
    Used by DiagnosticReport.presentedForm (0..*)."""

    contentType: str | None = None
    language: str | None = None
    data: str | None = None
    url: str | None = None
    size: int | None = None
    hash: str | None = None
    title: str | None = None
    creation: str | None = None


class FHIRDiagnosticReportSchema(BaseModel):
    resourceType: str = Field("DiagnosticReport", description="Always 'DiagnosticReport'.")
    id: str = Field(..., description="Public diagnostic_report_id as a string.")
    meta: FHIRMeta | None = Field(None, description="Infrastructure-maintained resource metadata. Response-only.")
    extension: list[dict] | None = Field(None, description="Resource-level FHIR extensions.")
    identifier: list[FHIRIdentifier] | None = Field(None, description="Business identifiers assigned to the report.")
    basedOn: list[FHIRReference] | None = Field(None, description="The request that was fulfilled by this report.")
    status: str = Field(..., description="registered | partial | preliminary | final | amended | corrected | appended | cancelled | entered-in-error | unknown.")
    category: list[FHIRCodeableConcept] | None = Field(None, description="Clinical service/discipline that produced the report.")
    code: FHIRCodeableConcept = Field(..., description="Name/code for this diagnostic report.")
    subject: FHIRReference | None = Field(None, description="The subject of the report, usually a patient.")
    encounter: FHIRReference | None = Field(None, description="Healthcare event during which this report was created.")
    effectiveDateTime: str | None = Field(None, description="effective[x]: dateTime.")
    effectivePeriod: FHIRPeriod | None = Field(None, description="effective[x]: Period.")
    issued: str | None = Field(None, description="When this version of the report was made available to providers.")
    performer: list[FHIRReference] | None = Field(None, description="Diagnostic service responsible for issuing the report.")
    resultsInterpreter: list[FHIRReference] | None = Field(None, description="Party responsible for the report's conclusions/interpretations.")
    specimen: list[FHIRReference] | None = Field(None, description="Specimens this report is based on.")
    result: list[FHIRReference] | None = Field(None, description="Observations that are part of this report.")
    imagingStudy: list[FHIRReference] | None = Field(None, description="Full details of imaging performed during the investigation.")
    media: list[FHIRDiagnosticReportMedia] | None = Field(None, description="Key images associated with this report.")
    conclusion: str | None = Field(None, description="Concise clinical summary/interpretation of the results.")
    conclusionCode: list[FHIRCodeableConcept] | None = Field(None, description="Codes for the clinical conclusion of this test.")
    presentedForm: list[FHIRDiagnosticReportAttachment] | None = Field(None, description="Full report as issued, e.g. a PDF.")


class FHIRDiagnosticReportBundleEntry(BaseModel):
    resource: FHIRDiagnosticReportSchema


class FHIRDiagnosticReportBundle(FHIRBundle):
    entry: list[FHIRDiagnosticReportBundleEntry] | None = None


# ── Plain (snake_case) ───────────────────────────────────────────────────────


class PlainDiagnosticReportResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public diagnostic_report_id.")
    extension: list[dict] | None = Field(None, description="Resource-level FHIR extensions.")
    identifier: list[PlainDiagnosticReportIdentifier] | None = Field(None, description="Business identifiers assigned to the report.")
    based_on: list[PlainDiagnosticReportBasedOn] | None = Field(None, description="The request that was fulfilled by this report.")
    status: str | None = Field(None, description="registered | partial | preliminary | final | amended | corrected | appended | cancelled | entered-in-error | unknown.")
    category: list[PlainDiagnosticReportCodeableConcept] | None = Field(None, description="Clinical service/discipline that produced the report.")
    code_codings: list[PlainCodingRow] | None = Field(None, description="Coding(s) for the report code.")
    code_text: str | None = Field(None, description="Text for the report code.")
    subject: PlainDiagnosticReportSubject | None = Field(None, description="The subject of the report, usually a patient.")
    encounter: PlainDiagnosticReportEncounter | None = Field(None, description="Healthcare event during which this report was created.")
    effective_date_time: str | None = Field(None, description="effective[x]: dateTime.")
    effective_period_start: str | None = Field(None, description="effective[x]: Period — start.")
    effective_period_end: str | None = Field(None, description="effective[x]: Period — end.")
    issued: str | None = Field(None, description="When this version of the report was made available to providers.")
    performer: list[PlainDiagnosticReportPerformer] | None = Field(None, description="Diagnostic service responsible for issuing the report.")
    results_interpreter: list[PlainDiagnosticReportResultsInterpreter] | None = Field(None, description="Party responsible for the report's conclusions/interpretations.")
    specimen: list[PlainDiagnosticReportSpecimen] | None = Field(None, description="Specimens this report is based on.")
    result: list[PlainDiagnosticReportResult] | None = Field(None, description="Observations that are part of this report.")
    imaging_study: list[PlainDiagnosticReportImagingStudy] | None = Field(None, description="Full details of imaging performed during the investigation.")
    media: list[PlainDiagnosticReportMedia] | None = Field(None, description="Key images associated with this report.")
    conclusion: str | None = Field(None, description="Concise clinical summary/interpretation of the results.")
    conclusion_code: list[PlainDiagnosticReportCodeableConcept] | None = Field(None, description="Codes for the clinical conclusion of this test.")
    presented_form: list[PlainDiagnosticReportPresentedForm] | None = Field(None, description="Full report as issued, e.g. a PDF.")
    user_id: str | None = Field(None, description="Gateway-forwarded end-user ID — not a FHIR concept.")
    org_id: str | None = Field(None, description="Gateway-forwarded tenant/account ID — not a FHIR concept. Internally this column is named tenant_id.")
    created_at: str | None = Field(None, description="When this row was created.")
    updated_at: str | None = Field(None, description="When this row was last updated.")
    created_by: str | None = Field(None, description="Acting user who created this record.")
    updated_by: str | None = Field(None, description="Acting user who last updated this record.")


class PaginatedDiagnosticReportResponse(BaseModel):
    total: int | None = Field(None, description="Total matching rows (null when total_mode=none).")
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Number of rows skipped before this page.")
    data: list[PlainDiagnosticReportResponse]
