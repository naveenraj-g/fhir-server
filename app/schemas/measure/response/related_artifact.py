from pydantic import BaseModel, ConfigDict, Field


class FHIRMeasureRelatedArtifact(BaseModel):
    """FHIR R4 RelatedArtifact representation."""

    model_config = ConfigDict(extra="allow")

    type: str = Field(..., description="RelatedArtifact.type.")
    label: str | None = None
    display: str | None = None
    citation: str | None = None
    url: str | None = None
    document: dict | None = None
    resource: str | None = None


class PlainMeasureRelatedArtifact(BaseModel):
    """Plain representation of a Measure related_artifact row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    type: str = Field(..., description="RelatedArtifact.type.")
    label: str | None = None
    display: str | None = None
    citation: str | None = None
    url: str | None = None
    document: dict | None = None
    resource: str | None = None
