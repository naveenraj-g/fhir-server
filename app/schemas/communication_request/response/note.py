from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import AuditFields
from app.schemas.datatypes.reference import FHIRReference


class FHIRCommunicationRequestAnnotation(BaseModel):
    """FHIR R4 Annotation element for CommunicationRequest.note."""

    model_config = ConfigDict(populate_by_name=True)

    authorString: str | None = None
    authorReference: FHIRReference | None = None
    time: str | None = None
    text: str


class PlainCommunicationRequestNote(AuditFields):
    """Plain snake_case serialization of a CommunicationRequest note child row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="DB primary key of this note row.")
    author_string: str | None = None
    author_reference: str | None = None
    author_type: str | None = None
    author_id: int | None = None
    author_display: str | None = None
    time: str | None = None
    text: str = Field(..., description="Annotation content.")
