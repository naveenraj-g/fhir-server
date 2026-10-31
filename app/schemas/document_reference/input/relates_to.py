from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import DocumentRelationshipType


class DocumentReferenceRelatesToInput(BaseModel):
    """DocumentReference.relatesTo entry."""

    model_config = ConfigDict(extra="forbid")
    code: DocumentRelationshipType = Field(
        ..., description="replaces | transforms | signs | appends"
    )
    target: str = Field(
        ..., description="Target of the relationship (e.g. 'DocumentReference/320000')."
    )
    target_display: str | None = Field(
        None, description="Display text for the target document reference."
    )
