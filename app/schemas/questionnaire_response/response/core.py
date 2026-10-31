from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRBundle, FHIRIdentifier, FHIRMeta, FHIRReference, PlainIdentifier

from .identifier import PlainQuestionnaireResponseIdentifier
from .item import FHIRQuestionnaireResponseItem, PlainQuestionnaireResponseItem
from .reference import (
    PlainQuestionnaireResponseAuthor,
    PlainQuestionnaireResponseBasedOn,
    PlainQuestionnaireResponseEncounter,
    PlainQuestionnaireResponsePartOf,
    PlainQuestionnaireResponseSource,
    PlainQuestionnaireResponseSubject,
)

# ── FHIR (camelCase) ────────────────────────────────────────────────────────


class FHIRQuestionnaireResponseSchema(BaseModel):
    resourceType: str = Field("QuestionnaireResponse", description="Always 'QuestionnaireResponse'.")
    id: str = Field(..., description="Public questionnaire_response_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries. Not yet validated against registered extension definitions.",
    )
    identifier: FHIRIdentifier | None = Field(None, description="A business identifier for this set of answers.")
    basedOn: list[FHIRReference] | None = Field(
        None, description="A plan, proposal, or order fulfilled in whole or in part by this QuestionnaireResponse."
    )
    partOf: list[FHIRReference] | None = Field(
        None, description="A procedure or observation this QuestionnaireResponse was performed as part of."
    )
    questionnaire: str | None = Field(None, description="Canonical reference to the Questionnaire this is for.")
    status: str = Field(..., description="in-progress | completed | amended | entered-in-error | stopped.")
    subject: FHIRReference | None = Field(None, description="Who/what the answers apply to.")
    encounter: FHIRReference | None = Field(None, description="The Encounter this was created during/for.")
    authored: str | None = Field(None, description="Date the answers were gathered or last changed.")
    author: FHIRReference | None = Field(None, description="Person who received and recorded the answers.")
    source: FHIRReference | None = Field(None, description="The person who answered the questions about the subject.")
    item: list[FHIRQuestionnaireResponseItem] | None = Field(None, description="Groups and questions, with their answers.")


class FHIRQuestionnaireResponseBundleEntry(BaseModel):
    resource: FHIRQuestionnaireResponseSchema


class FHIRQuestionnaireResponseBundle(FHIRBundle):
    entry: list[FHIRQuestionnaireResponseBundleEntry] | None = None


# ── Plain (snake_case) ───────────────────────────────────────────────────────


class PlainQuestionnaireResponseResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public questionnaire_response_id.")
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries."
    )
    identifier: PlainQuestionnaireResponseIdentifier | None = Field(
        None, description="A business identifier for this set of answers."
    )
    based_on: list[PlainQuestionnaireResponseBasedOn] | None = Field(
        None, description="A plan, proposal, or order fulfilled in whole or in part by this QuestionnaireResponse."
    )
    part_of: list[PlainQuestionnaireResponsePartOf] | None = Field(
        None, description="A procedure or observation this QuestionnaireResponse was performed as part of."
    )
    questionnaire: str | None = Field(None, description="Canonical reference to the Questionnaire this is for.")
    status: str | None = Field(None, description="in-progress | completed | amended | entered-in-error | stopped.")
    subject: PlainQuestionnaireResponseSubject | None = Field(None, description="Who/what the answers apply to.")
    encounter: PlainQuestionnaireResponseEncounter | None = Field(None, description="The Encounter this was created during/for.")
    authored: str | None = Field(None, description="Date the answers were gathered or last changed.")
    author: PlainQuestionnaireResponseAuthor | None = Field(None, description="Person who received and recorded the answers.")
    source: PlainQuestionnaireResponseSource | None = Field(None, description="The person who answered the questions about the subject.")
    item: list[PlainQuestionnaireResponseItem] | None = Field(None, description="Groups and questions, with their answers.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded ID of the tenant/account this record is scoped to (multi-tenancy) — not a FHIR concept. Internally this column is named tenant_id (see app/models/shared/tenant_audit.py) to avoid ambiguity with the Organization entity itself.",
    )
    created_at: str | None = Field(None, description="When this row was created.")
    updated_at: str | None = Field(None, description="When this row was last updated.")
    created_by: str | None = Field(None, description="Acting user who created this record.")
    updated_by: str | None = Field(None, description="Acting user who last updated this record.")


class PaginatedQuestionnaireResponseResponse(BaseModel):
    total: int | None = Field(None, description="Total matching rows (null when total_mode=none).")
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Number of rows skipped before this page.")
    data: list[PlainQuestionnaireResponseResponse]
