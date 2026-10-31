from pydantic import BaseModel, ConfigDict, Field


class FHIRPlanDefinitionGoal(BaseModel):
    """FHIR R4 PlanDefinition.goal."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    category: dict | None = None
    description: dict | None = None
    priority: dict | None = None
    start: dict | None = None
    addresses: list[dict] | None = None
    documentation: list[dict] | None = None
    target: list[dict] | None = None


class PlainPlanDefinitionGoal(BaseModel):
    """Plain PlanDefinition.goal representation."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    goal_id: str | None = None
    category: dict | None = None
    description: dict | None = None
    priority: dict | None = None
    start: dict | None = None
    addresses: list[dict] | None = None
    documentation: list[dict] | None = None
    target: list[dict] | None = None
