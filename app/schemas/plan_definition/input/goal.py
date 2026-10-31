from pydantic import BaseModel, ConfigDict, Field

from app.schemas.plan_definition.input.codeable_concept import (
    PlanDefinitionCodeableConceptInput,
)


class PlanDefinitionGoalInput(BaseModel):
    """PlanDefinition.goal input schema."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = Field(
        None, description="Element.id for internal cross-references."
    )
    goal_id: str | None = Field(
        None, description="Element.id for internal cross-references (alias)."
    )
    category: PlanDefinitionCodeableConceptInput | None = Field(
        None, description="E.g. Treatment, dietary, behavioral, etc."
    )
    description: PlanDefinitionCodeableConceptInput = Field(
        ..., description="Code or text describing the goal."
    )
    priority: PlanDefinitionCodeableConceptInput | None = Field(
        None, description="high-priority | medium-priority | low-priority."
    )
    start: PlanDefinitionCodeableConceptInput | None = Field(
        None, description="When goal pursuit begins."
    )
    addresses: list[PlanDefinitionCodeableConceptInput] | None = Field(
        None, description="Issues addressed by this goal."
    )
    documentation: list[dict] | None = Field(
        None, description="Supporting documentation for the goal."
    )
    target: list[dict] | None = Field(
        None, description="Target outcome for the goal."
    )
