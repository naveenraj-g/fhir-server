from pydantic import BaseModel, Field

from app.schemas.datatypes import FHIRReference


class FHIRPatientLink(BaseModel):
    """Patient.link — a link to another patient or related-person resource."""

    other: FHIRReference = Field(..., description="The other patient or related person resource that the link refers to.")
    type: str = Field(..., description="replaced-by | replaces | refer | seealso.")
