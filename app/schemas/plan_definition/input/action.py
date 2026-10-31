from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.plan_definition.enums import (
    PlanDefinitionActionCardinalityBehavior,
    PlanDefinitionActionGroupingBehavior,
    PlanDefinitionActionPrecheckBehavior,
    PlanDefinitionActionPriority,
    PlanDefinitionActionRequiredBehavior,
    PlanDefinitionActionSelectionBehavior,
)
from app.schemas.plan_definition.input.codeable_concept import (
    PlanDefinitionCodeableConceptInput,
)


class PlanDefinitionActionInput(BaseModel):
    """PlanDefinition.action (recursive) input schema."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = Field(
        None, description="Element.id for internal cross-references."
    )
    action_id_str: str | None = Field(
        None, description="Element.id for internal cross-references (alias)."
    )
    prefix: str | None = Field(None, description="User-visible prefix for the action (e.g. 1. or A.).")
    title: str | None = Field(None, description="User-visible title.")
    description: str | None = Field(None, description="Brief description of the action.")
    text_equivalent: str | None = Field(None, description="Static text equivalent of the action, used if the dynamic aspects cannot be interpreted by the receiving system.")
    priority: PlanDefinitionActionPriority | None = Field(None, description="routine | urgent | asap | stat.")
    code: list[dict] | None = Field(None, description="Code representing the meaning of the action or sub-actions.")
    reason: list[dict] | None = Field(None, description="Why the action should be performed.")
    documentation: list[dict] | None = Field(None, description="Supporting documentation for the action.")
    goal_id: list[str] | None = Field(None, description="What goals this action supports.")
    subject_codeable_concept: PlanDefinitionCodeableConceptInput | None = Field(None, description="Type of the subject of the action.")
    subject_reference: str | None = Field(None, description="Who or what the action is performed on, e.g. Group/123.")
    subject_display: str | None = Field(None, description="Plain text display for subject.")
    trigger: list[dict] | None = Field(None, description="When the action should be triggered.")
    condition: list[dict] | None = Field(None, description="Whether or not the action is applicable.")
    input: list[dict] | None = Field(None, description="Input data requirements.")
    output: list[dict] | None = Field(None, description="Output data requirements.")
    related_action: list[dict] | None = Field(None, description="Relationship to another action.")
    timing_date_time: datetime | None = Field(None, description="When the action should take place.")
    timing_age: dict | None = Field(None, description="Age when the action should take place.")
    timing_period_start: datetime | None = Field(None, description="Start of period when action should take place.")
    timing_period_end: datetime | None = Field(None, description="End of period when action should take place.")
    timing_duration: dict | None = Field(None, description="Duration when action should take place.")
    timing_range: dict | None = Field(None, description="Range when action should take place.")
    timing_timing: dict | None = Field(None, description="Timing schedule when action should take place.")
    participant: list[dict] | None = Field(None, description="Who should participate in the action.")
    type: PlanDefinitionCodeableConceptInput | None = Field(None, description="create | update | remove | fire-event.")
    grouping_behavior: PlanDefinitionActionGroupingBehavior | None = Field(None, description="visual-group | logical-group | sentence-group.")
    selection_behavior: PlanDefinitionActionSelectionBehavior | None = Field(None, description="any | all | all-or-none | exactly-one | at-most-one | one-or-more.")
    required_behavior: PlanDefinitionActionRequiredBehavior | None = Field(None, description="must | could | must-unless-documented.")
    precheck_behavior: PlanDefinitionActionPrecheckBehavior | None = Field(None, description="yes | no.")
    cardinality_behavior: PlanDefinitionActionCardinalityBehavior | None = Field(None, description="single | multiple.")
    definition_canonical: str | None = Field(None, description="Description of the activity to be performed (canonical URI).")
    definition_uri: str | None = Field(None, description="Description of the activity to be performed (URI).")
    transform: str | None = Field(None, description="Transform to apply the template (canonical URI).")
    dynamic_value: list[dict] | None = Field(None, description="Dynamic aspects of the content.")
    action: list["PlanDefinitionActionInput"] | None = Field(None, description="Sub-action (recursive).")


PlanDefinitionActionInput.model_rebuild()
