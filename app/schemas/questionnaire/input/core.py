from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput
from app.schemas.enums import QuestionnaireStatus

from .contact import QuestionnaireContactInput
from .identifier import QuestionnaireIdentifierInput
from .item import QuestionnaireItemInput
from .jurisdiction import QuestionnaireJurisdictionInput
from .use_context import QuestionnaireUseContextInput


class QuestionnaireCreateSchema(BaseModel):
    """Creates a Questionnaire and any combination of its sub-resource
    lists atomically in one request — same set-once-then-patch shape as
    every other resource in this codebase.

    Questionnaire now gets the JWT-auth-rollout treatment (see CLAUDE.md's
    Multi-Tenancy & Ownership section and `/resource-auth-rollout`):
    `tenant_id` and `created_by` come from the verified JWT
    (`actor.org_id`/`actor.sub`) and are therefore NOT request-body
    fields at all — a caller who still sends either gets a clean 422
    (`extra="forbid"`). `user_id` is unaffected — still a plain, optional,
    gateway-forwarded field, same as Practitioner's own `user_id`.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-001",
                "url": "https://fhir-server.dev/fhir/Questionnaire/intake-form",
                "version": "1.0.0",
                "name": "IntakeForm",
                "title": "Patient Intake Form",
                "status": "active",
                "subject_type": ["Patient"],
                "item": [
                    {
                        "link_id": "1",
                        "text": "Do you have any allergies?",
                        "type": "boolean",
                    },
                    {
                        "link_id": "2",
                        "text": "General Information",
                        "type": "group",
                        "item": [
                            {
                                "link_id": "2.1",
                                "text": "What is your name?",
                                "type": "string",
                                "required": True,
                            }
                        ],
                    },
                ],
            }
        },
    )

    user_id: str | None = Field(
        None, description="Gateway-forwarded ID of the end-user this record is scoped to — not a FHIR concept."
    )

    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries. Not yet validated against registered extension definitions.",
    )

    url: str | None = Field(
        None, description="Canonical identifier for this questionnaire, globally unique."
    )
    identifier: list[QuestionnaireIdentifierInput] | None = Field(
        None, description="Additional identifiers for this questionnaire."
    )
    version: str | None = Field(None, description="Business version of the questionnaire.")
    name: str | None = Field(
        None, description="Computer-friendly name for this questionnaire — should be usable as a code-generation identifier."
    )
    title: str | None = Field(None, description="Human-friendly name for this questionnaire.")
    derived_from: list[str] | None = Field(
        None, description="The URL(s) of Questionnaire(s) this one is based on, as canonical references."
    )

    # status (1..1) — required
    status: QuestionnaireStatus = Field(
        ..., description="draft | active | retired | unknown."
    )

    experimental: bool | None = Field(
        None, description="Whether this is meant for testing purposes (or real usage)."
    )
    subject_type: list[str] | None = Field(
        None, description="Resource type(s) that can be the subject of a QuestionnaireResponse."
    )
    date: datetime | None = Field(None, description="Date this was last changed.")
    publisher: str | None = Field(None, description="Name of the publishing organization or individual.")
    description: str | None = Field(None, description="Natural-language description of the questionnaire (markdown).")
    purpose: str | None = Field(None, description="Why this questionnaire is defined (markdown).")
    copyright: str | None = Field(None, description="Use and/or publishing restrictions (markdown).")
    approval_date: date_type | None = Field(None, description="When the questionnaire was approved by publisher.")
    last_review_date: date_type | None = Field(None, description="When the questionnaire was last reviewed.")
    effective_period_start: datetime | None = Field(
        None, description="Start of the period during which this questionnaire version is in active use."
    )
    effective_period_end: datetime | None = Field(
        None, description="End of the period during which this questionnaire version is in active use."
    )

    code: list[CodingInput] | None = Field(
        None, description="Concept(s) that represent the overall questionnaire (e.g. a LOINC code)."
    )

    contact: list[QuestionnaireContactInput] | None = Field(
        None, description="Contact details for the publisher."
    )
    use_context: list[QuestionnaireUseContextInput] | None = Field(
        None, description="The context that the content is intended to support."
    )
    jurisdiction: list[QuestionnaireJurisdictionInput] | None = Field(
        None, description="Intended jurisdiction(s) for questionnaire (if applicable)."
    )

    item: list[QuestionnaireItemInput] | None = Field(
        None, description="Questions and sections within this questionnaire."
    )


class QuestionnairePatchSchema(BaseModel):
    """Partial update — only supplied fields are written. Every supplied
    sub-resource list (even `[]`) replaces the corresponding rows wholesale;
    omitted lists are left untouched. `tenant_id`/`created_by`/`updated_by`
    are all immutable/derived-from-the-JWT and excluded here — see
    QuestionnaireCreateSchema's docstring."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "retired",
            }
        },
    )

    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries — replaces the full list if supplied.",
    )

    url: str | None = Field(None, description="Canonical identifier. Set to null to clear.")
    identifier: list[QuestionnaireIdentifierInput] | None = Field(
        None, description="Additional identifiers — replaces the full list if supplied."
    )
    version: str | None = Field(None, description="Business version of the questionnaire.")
    name: str | None = Field(None, description="Computer-friendly name.")
    title: str | None = Field(None, description="Human-friendly name.")
    derived_from: list[str] | None = Field(
        None, description="Canonical references to Questionnaire(s) this one is based on — replaces the full list if supplied."
    )

    status: QuestionnaireStatus | None = Field(
        None, description="draft | active | retired | unknown."
    )

    experimental: bool | None = Field(None, description="Whether this is meant for testing purposes.")
    subject_type: list[str] | None = Field(
        None, description="Resource type(s) that can be the subject of a QuestionnaireResponse — replaces the full list if supplied."
    )
    date: datetime | None = Field(None, description="Date this was last changed.")
    publisher: str | None = Field(None, description="Name of the publishing organization or individual.")
    description: str | None = Field(None, description="Natural-language description (markdown).")
    purpose: str | None = Field(None, description="Why this questionnaire is defined (markdown).")
    copyright: str | None = Field(None, description="Use and/or publishing restrictions (markdown).")
    approval_date: date_type | None = Field(None, description="When the questionnaire was approved by publisher.")
    last_review_date: date_type | None = Field(None, description="When the questionnaire was last reviewed.")
    effective_period_start: datetime | None = Field(None, description="Start of the active-use period.")
    effective_period_end: datetime | None = Field(None, description="End of the active-use period.")

    code: list[CodingInput] | None = Field(
        None, description="Concept(s) representing the overall questionnaire — replaces the full list if supplied."
    )

    contact: list[QuestionnaireContactInput] | None = Field(
        None, description="Contact details for the publisher — replaces the full list if supplied."
    )
    use_context: list[QuestionnaireUseContextInput] | None = Field(
        None, description="Context the content is intended to support — replaces the full list if supplied."
    )
    jurisdiction: list[QuestionnaireJurisdictionInput] | None = Field(
        None, description="Intended jurisdiction(s) — replaces the full list if supplied."
    )

    item: list[QuestionnaireItemInput] | None = Field(
        None, description="Questions and sections — replaces the full tree if supplied."
    )
