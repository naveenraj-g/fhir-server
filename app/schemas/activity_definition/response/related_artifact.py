from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRAttachment


class FHIRActivityDefinitionRelatedArtifact(BaseModel):
    """FHIR R4 RelatedArtifact."""

    model_config = ConfigDict(extra="allow")

    type: str | None = None
    label: str | None = None
    display: str | None = None
    citation: str | None = None
    url: str | None = None
    document: FHIRAttachment | None = None
    resource: str | None = None


class PlainActivityDefinitionRelatedArtifact(BaseModel):
    """Plain RelatedArtifact representation."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    type: str = Field(..., description="Related artifact type.")
    label: str | None = None
    display: str | None = None
    citation: str | None = None
    url: str | None = None
    document: dict | None = None
    resource: str | None = None
