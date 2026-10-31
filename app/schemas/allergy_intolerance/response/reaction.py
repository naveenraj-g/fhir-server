from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.allergy_intolerance.response.codeable_concept import (
    PlainAllergyIntoleranceCodeableConcept,
)
from app.schemas.allergy_intolerance.response.note import (
    PlainAllergyIntoleranceNote,
)
from app.schemas.datatypes import FHIRCodeableConcept


class FHIRAllergyIntoleranceReaction(BaseModel):
    """FHIR R4 representation of AllergyIntolerance.reaction."""

    model_config = ConfigDict(extra="allow")

    substance: FHIRCodeableConcept | None = None
    manifestation: list[FHIRCodeableConcept]
    description: str | None = None
    onset: str | None = None
    severity: str | None = None
    exposureRoute: FHIRCodeableConcept | None = None
    note: list[dict[str, Any]] | None = None


class PlainAllergyIntoleranceReaction(BaseModel):
    """Plain snake_case representation of AllergyIntolerance reaction child row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    substance: PlainAllergyIntoleranceCodeableConcept | None = None
    manifestation: list[PlainAllergyIntoleranceCodeableConcept] = Field(
        ..., description="Clinical symptoms/signs associated with the Event."
    )
    description: str | None = None
    onset: datetime | None = None
    severity: str | None = None
    exposure_route: PlainAllergyIntoleranceCodeableConcept | None = None
    note: list[PlainAllergyIntoleranceNote] | None = None
