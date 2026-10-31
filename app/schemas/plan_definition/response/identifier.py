from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCodingRow


class PlainPlanDefinitionIdentifier(BaseModel):
    """Plain PlanDefinition.identifier representation."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal DB ID.")
    use: str | None = None
    system: str | None = None
    value: str | None = None
    type_text: str | None = None
    type_codings: list[PlainCodingRow] | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    assigner: str | None = None
    assigner_display: str | None = None
