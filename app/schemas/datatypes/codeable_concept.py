from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.datatypes.coding import FHIRCoding


class FHIRCodeableConcept(BaseModel):
    """FHIR R4 CodeableConcept — a concept expressed as one or more coded terms
    plus a plain-text representation."""

    coding: Optional[List[FHIRCoding]] = Field(
        None, description="Code(s) defined by a terminology system for this concept."
    )
    text: Optional[str] = Field(
        None, description="Plain-text representation of the concept, for display when coding is not understood."
    )
