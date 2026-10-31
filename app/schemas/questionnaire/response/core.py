from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCoding,
    FHIRIdentifier,
    FHIRMeta,
    PlainCodingRow,
)

from .contact import FHIRQuestionnaireContact, PlainQuestionnaireContact
from .fhir_item import FHIRQuestionnaireItem
from .identifier import PlainQuestionnaireIdentifier
from .item import PlainQuestionnaireItem
from .jurisdiction import PlainQuestionnaireJurisdiction
from .use_context import FHIRQuestionnaireUseContext, PlainQuestionnaireUseContext

# ── FHIR (camelCase) ────────────────────────────────────────────────────────


class FHIRQuestionnaireJurisdiction(BaseModel):
    coding: list[FHIRCoding] | None = None
    text: str | None = None


class FHIRQuestionnaireSchema(BaseModel):
    resourceType: str = Field("Questionnaire", description="Always 'Questionnaire'.")
    id: str = Field(..., description="Public questionnaire_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's tenant_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries. Not yet validated against registered extension definitions.",
    )
    url: str | None = Field(None, description="Canonical identifier for this questionnaire.")
    identifier: list[FHIRIdentifier] | None = Field(None, description="Additional identifiers.")
    version: str | None = Field(None, description="Business version.")
    name: str | None = Field(None, description="Computer-friendly name.")
    title: str | None = Field(None, description="Human-friendly name.")
    derivedFrom: list[str] | None = Field(None, description="Canonical references to Questionnaire(s) this is based on.")
    status: str = Field(..., description="draft | active | retired | unknown.")
    experimental: bool | None = Field(None, description="Authored for testing, not real usage.")
    subjectType: list[str] | None = Field(None, description="Resource type(s) that can be the subject of a QuestionnaireResponse.")
    date: str | None = Field(None, description="Date last changed.")
    publisher: str | None = Field(None, description="Publishing organization or individual.")
    description: str | None = Field(None, description="Natural-language description (markdown).")
    purpose: str | None = Field(None, description="Why the questionnaire exists (markdown).")
    copyright: str | None = Field(None, description="Use and publishing restrictions (markdown).")
    approvalDate: str | None = Field(None, description="Date approved by publisher.")
    lastReviewDate: str | None = Field(None, description="Date last reviewed.")
    effectivePeriod: dict | None = Field(None, description="When it is expected to be in use.")
    code: list[FHIRCoding] | None = Field(None, description="Concept representing the overall questionnaire.")
    contact: list[FHIRQuestionnaireContact] | None = Field(None, description="Publisher contact details.")
    useContext: list[FHIRQuestionnaireUseContext] | None = Field(None, description="Intended usage contexts.")
    jurisdiction: list[FHIRQuestionnaireJurisdiction] | None = Field(None, description="Intended jurisdiction.")
    item: list[FHIRQuestionnaireItem] | None = Field(None, description="Questions and sections.")


class FHIRQuestionnaireBundleEntry(BaseModel):
    resource: FHIRQuestionnaireSchema


class FHIRQuestionnaireBundle(FHIRBundle):
    entry: list[FHIRQuestionnaireBundleEntry] | None = None


# ── Plain (snake_case) ───────────────────────────────────────────────────────


class PlainQuestionnaireResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public questionnaire_id.")
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries.",
    )
    url: str | None = Field(None, description="Canonical identifier for this questionnaire.")
    identifier: list[PlainQuestionnaireIdentifier] | None = Field(None, description="Additional identifiers.")
    version: str | None = Field(None, description="Business version.")
    name: str | None = Field(None, description="Computer-friendly name.")
    title: str | None = Field(None, description="Human-friendly name.")
    derived_from: list[str] | None = Field(None, description="Canonical references to Questionnaire(s) this is based on.")
    status: str | None = Field(None, description="draft | active | retired | unknown.")
    experimental: bool | None = Field(None, description="Authored for testing, not real usage.")
    subject_type: list[str] | None = Field(None, description="Resource type(s) that can be the subject of a QuestionnaireResponse.")
    date: str | None = Field(None, description="Date last changed.")
    publisher: str | None = Field(None, description="Publishing organization or individual.")
    description: str | None = Field(None, description="Natural-language description (markdown).")
    purpose: str | None = Field(None, description="Why the questionnaire exists (markdown).")
    copyright: str | None = Field(None, description="Use and publishing restrictions (markdown).")
    approval_date: str | None = Field(None, description="Date approved by publisher.")
    last_review_date: str | None = Field(None, description="Date last reviewed.")
    effective_period_start: str | None = Field(None, description="Start of the active-use period.")
    effective_period_end: str | None = Field(None, description="End of the active-use period.")
    codings: list[PlainCodingRow] | None = Field(None, description="Concept(s) representing the overall questionnaire.")
    contact: list[PlainQuestionnaireContact] | None = Field(None, description="Publisher contact details.")
    use_context: list[PlainQuestionnaireUseContext] | None = Field(None, description="Intended usage contexts.")
    jurisdiction: list[PlainQuestionnaireJurisdiction] | None = Field(None, description="Intended jurisdiction.")
    item: list[PlainQuestionnaireItem] | None = Field(None, description="Questions and sections.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded ID of the tenant/account this record is scoped to (multi-tenancy) — not a FHIR concept. Internally this column is named tenant_id (see app/models/shared/tenant_audit.py) to avoid ambiguity with the Organization entity itself; the external field name stays org_id for consistency with every other auth-rollout resource's response contract.",
    )
    created_at: str | None = Field(None, description="When this row was created.")
    updated_at: str | None = Field(None, description="When this row was last updated.")
    created_by: str | None = Field(None, description="Acting user who created this record.")
    updated_by: str | None = Field(None, description="Acting user who last updated this record.")


class PaginatedQuestionnaireResponse(BaseModel):
    total: int | None = Field(None, description="Total matching rows (null when total_mode=none).")
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Number of rows skipped before this page.")
    data: list[PlainQuestionnaireResponse]
