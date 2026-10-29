from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import QuestionnaireResponseStatus

from .identifier import QuestionnaireResponseIdentifierInput
from .item import QuestionnaireResponseItemInput
from .reference import (
    QuestionnaireResponseAuthorInput,
    QuestionnaireResponseBasedOnInput,
    QuestionnaireResponseEncounterInput,
    QuestionnaireResponsePartOfInput,
    QuestionnaireResponseSourceInput,
    QuestionnaireResponseSubjectInput,
)


class QuestionnaireResponseCreateSchema(BaseModel):
    """Creates a QuestionnaireResponse and any combination of its
    sub-resource lists atomically in one request — same set-once-then-patch
    shape as every other resource in this codebase.

    Default (gateway-trusted) pattern — NOT part of the JWT auth rollout
    (see CLAUDE.md's Multi-Tenancy & Ownership section): `tenant_id` and
    `created_by` are plain, gateway-forwarded request fields here, unlike
    every currently-built resource (all of which have since been
    individually rolled into the auth-rollout pattern) — this is the first
    new resource built since then, so it's the live example of the plain
    default pattern CLAUDE.md always described but had no current example
    of. `user_id` behaves the same either way."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-001",
                "tenant_id": "org-001",
                "created_by": "user-001",
                "questionnaire": "https://fhir-server.dev/fhir/Questionnaire/intake-form",
                "status": "completed",
                "authored": "2026-01-15T10:30:00Z",
                "item": [
                    {
                        "link_id": "1",
                        "text": "Do you have any allergies?",
                        "answer": [{"value_boolean": False}],
                    }
                ],
            }
        },
    )

    user_id: str | None = Field(
        None, description="Gateway-forwarded ID of the end-user this record is scoped to — not a FHIR concept."
    )
    tenant_id: str = Field(
        ..., description="Gateway-forwarded ID of the tenant/account this record is scoped to (multi-tenancy) — not a FHIR concept."
    )
    created_by: str = Field(
        ..., description="Gateway-forwarded ID of the acting user who created this record — not a FHIR concept."
    )

    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries. Not yet validated against registered extension definitions.",
    )

    identifier: QuestionnaireResponseIdentifierInput | None = Field(
        None, description="A business identifier for this set of answers."
    )
    based_on: list[QuestionnaireResponseBasedOnInput] | None = Field(
        None, description="A plan, proposal, or order fulfilled in whole or in part by this QuestionnaireResponse."
    )
    part_of: list[QuestionnaireResponsePartOfInput] | None = Field(
        None, description="A procedure or observation this QuestionnaireResponse was performed as part of."
    )
    questionnaire: str | None = Field(
        None, description="The Questionnaire this set of answers is for, as a canonical reference (uri)."
    )

    # status (1..1) — required
    status: QuestionnaireResponseStatus = Field(
        ..., description="in-progress | completed | amended | entered-in-error | stopped."
    )

    subject: QuestionnaireResponseSubjectInput | None = Field(
        None, description="The subject of the questions (who/what the answers apply to)."
    )
    encounter: QuestionnaireResponseEncounterInput | None = Field(
        None, description="The Encounter during which this QuestionnaireResponse was created."
    )
    authored: datetime | None = Field(None, description="Date the answers were gathered or last changed.")
    author: QuestionnaireResponseAuthorInput | None = Field(
        None, description="Person who received and recorded the answers."
    )
    source: QuestionnaireResponseSourceInput | None = Field(
        None, description="The person who answered the questions about the subject."
    )

    item: list[QuestionnaireResponseItemInput] | None = Field(
        None, description="Groups and questions, with their answers."
    )


class QuestionnaireResponsePatchSchema(BaseModel):
    """Partial update — only supplied fields are written. Every supplied
    sub-resource list (even `[]`) replaces the corresponding rows wholesale;
    omitted lists are left untouched. `tenant_id`/`created_by` are
    immutable and excluded here; `updated_by` is a plain, optional,
    gateway-forwarded field (default pattern — see
    QuestionnaireResponseCreateSchema's docstring)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"updated_by": "user-001", "status": "amended"}},
    )

    updated_by: str | None = Field(
        None, description="Gateway-forwarded ID of the acting user making this update — not a FHIR concept."
    )

    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries — replaces the full list if supplied.",
    )

    identifier: QuestionnaireResponseIdentifierInput | None = Field(
        None, description="A business identifier for this set of answers. Set to null to clear."
    )
    based_on: list[QuestionnaireResponseBasedOnInput] | None = Field(
        None, description="Replaces the full list if supplied."
    )
    part_of: list[QuestionnaireResponsePartOfInput] | None = Field(
        None, description="Replaces the full list if supplied."
    )
    questionnaire: str | None = Field(None, description="Canonical reference to the Questionnaire. Set to null to clear.")

    status: QuestionnaireResponseStatus | None = Field(
        None, description="in-progress | completed | amended | entered-in-error | stopped."
    )

    subject: QuestionnaireResponseSubjectInput | None = Field(None, description="Set to null to clear.")
    encounter: QuestionnaireResponseEncounterInput | None = Field(None, description="Set to null to clear.")
    authored: datetime | None = Field(None, description="Date the answers were gathered or last changed.")
    author: QuestionnaireResponseAuthorInput | None = Field(None, description="Set to null to clear.")
    source: QuestionnaireResponseSourceInput | None = Field(None, description="Set to null to clear.")

    item: list[QuestionnaireResponseItemInput] | None = Field(
        None, description="Groups/questions with their answers — replaces the full tree if supplied."
    )
