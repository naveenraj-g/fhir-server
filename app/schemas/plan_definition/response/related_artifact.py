from pydantic import BaseModel, ConfigDict, Field


class FHIRPlanDefinitionRelatedArtifact(BaseModel):
    """FHIR R4 RelatedArtifact."""

    model_config = ConfigDict(extra="allow")

    type: str
    label: str | None = None
    display: str | None = None
    citation: str | None = None
    url: str | None = None
    document: dict | None = None
    resource: str | None = None


class PlainPlanDefinitionRelatedArtifact(BaseModel):
    """Plain RelatedArtifact representation."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    type: str
    label: str | None = None
    display: str | None = None
    citation: str | None = None
    url: str | None = None
    document: dict | None = None
    resource: str | None = None
