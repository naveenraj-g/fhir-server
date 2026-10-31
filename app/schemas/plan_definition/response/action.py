from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FHIRPlanDefinitionAction(BaseModel):
    """FHIR R4 PlanDefinition.action."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    prefix: str | None = None
    title: str | None = None
    description: str | None = None
    textEquivalent: str | None = None
    priority: str | None = None
    code: list[dict] | None = None
    reason: list[dict] | None = None
    documentation: list[dict] | None = None
    goalId: list[str] | None = None
    subjectCodeableConcept: dict | None = None
    subjectReference: dict | None = None
    trigger: list[dict] | None = None
    condition: list[dict] | None = None
    input: list[dict] | None = None
    output: list[dict] | None = None
    relatedAction: list[dict] | None = None
    timingDateTime: str | None = None
    timingAge: dict | None = None
    timingPeriod: dict | None = None
    timingDuration: dict | None = None
    timingRange: dict | None = None
    timingTiming: dict | None = None
    participant: list[dict] | None = None
    type: dict | None = None
    groupingBehavior: str | None = None
    selectionBehavior: str | None = None
    requiredBehavior: str | None = None
    precheckBehavior: str | None = None
    cardinalityBehavior: str | None = None
    definitionCanonical: str | None = None
    definitionUri: str | None = None
    transform: str | None = None
    dynamicValue: list[dict] | None = None
    action: list["FHIRPlanDefinitionAction"] | None = None


FHIRPlanDefinitionAction.model_rebuild()


class PlainPlanDefinitionAction(BaseModel):
    """Plain PlanDefinition.action representation."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    action_id_str: str | None = None
    prefix: str | None = None
    title: str | None = None
    description: str | None = None
    text_equivalent: str | None = None
    priority: str | None = None
    code: list[dict] | None = None
    reason: list[dict] | None = None
    documentation: list[dict] | None = None
    goal_id: list[str] | None = None
    subject_codeable_concept_text: str | None = None
    subject_reference: str | None = None
    subject_display: str | None = None
    trigger: list[dict] | None = None
    condition: list[dict] | None = None
    input: list[dict] | None = None
    output: list[dict] | None = None
    related_action: list[dict] | None = None
    timing_date_time: datetime | None = None
    timing_age: dict | None = None
    timing_period_start: datetime | None = None
    timing_period_end: datetime | None = None
    timing_duration: dict | None = None
    timing_range: dict | None = None
    timing_timing: dict | None = None
    participant: list[dict] | None = None
    type_text: str | None = None
    type_codings: list[dict] | None = None
    grouping_behavior: str | None = None
    selection_behavior: str | None = None
    required_behavior: str | None = None
    precheck_behavior: str | None = None
    cardinality_behavior: str | None = None
    definition_canonical: str | None = None
    definition_uri: str | None = None
    transform: str | None = None
    dynamic_value: list[dict] | None = None
    action: list["PlainPlanDefinitionAction"] | None = None


PlainPlanDefinitionAction.model_rebuild()
