from pydantic import BaseModel, ConfigDict, Field

from app.models.plan_definition.enums import PlanDefinitionRelatedArtifactType


class PlanDefinitionRelatedArtifactInput(BaseModel):
    """PlanDefinition.relatedArtifact input schema."""

    model_config = ConfigDict(extra="forbid")

    type: PlanDefinitionRelatedArtifactType = Field(
        ...,
        description="documentation | justification | citation | predecessor | successor | derived-from | depends-on | composed-of.",
    )
    label: str | None = Field(None, description="Short label.")
    display: str | None = Field(None, description="Brief description of the related artifact.")
    citation: str | None = Field(None, description="Bibliographic citation for the artifact.")
    url: str | None = Field(None, description="Where the artifact can be accessed.")
    document: dict | None = Field(None, description="What document is being referenced (Attachment).")
    resource: str | None = Field(None, description="What document is being referenced (canonical reference).")
