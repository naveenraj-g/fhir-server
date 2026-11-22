from pydantic import BaseModel, Field

from app.schemas.datatypes.reference import FHIRReference


class FHIRAnnotation(BaseModel):
    """FHIR R4 Annotation. `authorReference` / `authorString` are the two `author[x]`
    variants."""

    authorReference: FHIRReference | None = None
    authorString: str | None = None
    time: str | None = None
    text: str = Field(..., description="The annotation text (markdown).")
