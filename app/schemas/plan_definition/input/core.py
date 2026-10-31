import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.models.plan_definition.enums import PlanDefinitionStatus
from app.schemas.plan_definition.input.action import PlanDefinitionActionInput
from app.schemas.plan_definition.input.codeable_concept import (
    PlanDefinitionCodeableConceptInput,
)
from app.schemas.plan_definition.input.contact import PlanDefinitionContactInput
from app.schemas.plan_definition.input.goal import PlanDefinitionGoalInput
from app.schemas.plan_definition.input.identifier import (
    PlanDefinitionIdentifierInput,
)
from app.schemas.plan_definition.input.related_artifact import (
    PlanDefinitionRelatedArtifactInput,
)
from app.schemas.plan_definition.input.use_context import (
    PlanDefinitionUseContextInput,
)


class PlanDefinitionCreateSchema(BaseModel):
    """Request body for creating a PlanDefinition resource."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "draft",
                "name": "DiabetesManagementProtocol",
                "title": "Protocol for Glycemic Control",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/plan-definition-type",
                            "code": "clinical-protocol",
                            "display": "Clinical Protocol",
                        }
                    ],
                    "text": "Clinical Protocol",
                },
                "description": "Standardized clinical care protocol for glycemic management in Type 2 Diabetes.",
            }
        },
    )

    status: PlanDefinitionStatus = Field(
        ..., description="draft | active | retired | unknown."
    )
    url: str | None = Field(
        None, description="Canonical identifier for this plan definition, represented as a URI."
    )
    version: str | None = Field(
        None, description="Business version of the plan definition."
    )
    name: str | None = Field(
        None, description="Name for this plan definition (computer friendly)."
    )
    title: str | None = Field(
        None, description="Name for this plan definition (human friendly)."
    )
    subtitle: str | None = Field(
        None, description="Subordinate title of the plan definition."
    )
    type: PlanDefinitionCodeableConceptInput | None = Field(
        None, description="order-set | clinical-protocol | eca-rule | workflow-definition."
    )
    experimental: bool | None = Field(
        None, description="For testing purposes, not real usage."
    )
    subject_codeable_concept: PlanDefinitionCodeableConceptInput | None = Field(
        None, description="Type of the subject of the plan definition."
    )
    subject_reference: str | None = Field(
        None, description="Who or what the plan definition is for (Reference(Group))."
    )
    subject_display: str | None = Field(
        None, description="Plain text display for subject."
    )
    date: dt.datetime | None = Field(
        None, description="Date last changed."
    )
    publisher: str | None = Field(
        None, description="Name of the publisher (organization or individual)."
    )
    description: str | None = Field(
        None, description="Natural language description of the plan definition."
    )
    purpose: str | None = Field(
        None, description="Why this plan definition is defined."
    )
    usage: str | None = Field(
        None, description="Describes the clinical usage of the plan."
    )
    copyright: str | None = Field(
        None, description="Use and/or publishing restrictions."
    )
    approval_date: dt.date | None = Field(
        None, description="When the plan definition was approved by publisher."
    )
    last_review_date: dt.date | None = Field(
        None, description="When the plan definition was last reviewed."
    )
    effective_period_start: dt.datetime | None = Field(
        None, description="When the plan definition is expected to be used."
    )
    effective_period_end: dt.datetime | None = Field(
        None, description="When the plan definition is expected to be used."
    )
    library: list[str] | None = Field(
        None, description="Logic used by the plan definition (canonical URLs)."
    )
    extension: list[dict] | None = Field(
        None, description="Additional content defined by implementations."
    )

    # Sub-resource lists
    identifier: list[PlanDefinitionIdentifierInput] | None = Field(
        None, description="Additional identifier for the plan definition."
    )
    contact: list[PlanDefinitionContactInput] | None = Field(
        None, description="Contact details for the publisher."
    )
    author: list[PlanDefinitionContactInput] | None = Field(
        None, description="Who authored the content."
    )
    editor: list[PlanDefinitionContactInput] | None = Field(
        None, description="Who edited the content."
    )
    reviewer: list[PlanDefinitionContactInput] | None = Field(
        None, description="Who reviewed the content."
    )
    endorser: list[PlanDefinitionContactInput] | None = Field(
        None, description="Who endorsed the content."
    )
    use_context: list[PlanDefinitionUseContextInput] | None = Field(
        None, description="The context that the content is intended to support."
    )
    jurisdiction: list[PlanDefinitionCodeableConceptInput] | None = Field(
        None, description="Intended jurisdiction for plan definition."
    )
    topic: list[PlanDefinitionCodeableConceptInput] | None = Field(
        None, description="E.g. Education, Treatment, Assessment, etc."
    )
    related_artifact: list[PlanDefinitionRelatedArtifactInput] | None = Field(
        None, description="Additional documentation, citations, etc."
    )
    goal: list[PlanDefinitionGoalInput] | None = Field(
        None, description="What the plan is trying to accomplish."
    )
    action: list[PlanDefinitionActionInput] | None = Field(
        None, description="Action defined by the plan."
    )


class PlanDefinitionPatchSchema(BaseModel):
    """Request body for patching a PlanDefinition resource. All fields optional."""

    model_config = ConfigDict(extra="forbid")

    status: PlanDefinitionStatus | None = Field(None, description="draft | active | retired | unknown.")
    url: str | None = Field(None, description="Canonical identifier.")
    version: str | None = Field(None, description="Business version.")
    name: str | None = Field(None, description="Computer-friendly name.")
    title: str | None = Field(None, description="Human-friendly title.")
    subtitle: str | None = Field(None, description="Subordinate title.")
    type: PlanDefinitionCodeableConceptInput | None = Field(None, description="Type of plan.")
    experimental: bool | None = Field(None, description="For testing purposes.")
    subject_codeable_concept: PlanDefinitionCodeableConceptInput | None = Field(None, description="Subject concept.")
    subject_reference: str | None = Field(None, description="Subject reference (Group/123).")
    subject_display: str | None = Field(None, description="Plain text display for subject.")
    date: dt.datetime | None = Field(None, description="Date last changed.")
    publisher: str | None = Field(None, description="Publisher name.")
    description: str | None = Field(None, description="Natural language description.")
    purpose: str | None = Field(None, description="Why defined.")
    usage: str | None = Field(None, description="Clinical usage.")
    copyright: str | None = Field(None, description="Copyright statement.")
    approval_date: dt.date | None = Field(None, description="Approval date.")
    last_review_date: dt.date | None = Field(None, description="Last review date.")
    effective_period_start: dt.datetime | None = Field(None, description="Effective start.")
    effective_period_end: dt.datetime | None = Field(None, description="Effective end.")
    library: list[str] | None = Field(None, description="Logic libraries.")
    extension: list[dict] | None = Field(None, description="Extensions.")

    identifier: list[PlanDefinitionIdentifierInput] | None = Field(None, description="Identifiers.")
    contact: list[PlanDefinitionContactInput] | None = Field(None, description="Contacts.")
    author: list[PlanDefinitionContactInput] | None = Field(None, description="Authors.")
    editor: list[PlanDefinitionContactInput] | None = Field(None, description="Editors.")
    reviewer: list[PlanDefinitionContactInput] | None = Field(None, description="Reviewers.")
    endorser: list[PlanDefinitionContactInput] | None = Field(None, description="Endorsers.")
    use_context: list[PlanDefinitionUseContextInput] | None = Field(None, description="Contexts.")
    jurisdiction: list[PlanDefinitionCodeableConceptInput] | None = Field(None, description="Jurisdictions.")
    topic: list[PlanDefinitionCodeableConceptInput] | None = Field(None, description="Topics.")
    related_artifact: list[PlanDefinitionRelatedArtifactInput] | None = Field(None, description="Related artifacts.")
    goal: list[PlanDefinitionGoalInput] | None = Field(None, description="Goals.")
    action: list[PlanDefinitionActionInput] | None = Field(None, description="Actions.")
