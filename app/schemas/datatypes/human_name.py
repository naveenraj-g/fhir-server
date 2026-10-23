from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.datatypes.period import FHIRPeriod


class FHIRHumanName(BaseModel):
    """FHIR R4 HumanName — a name associated with an individual."""

    use: Optional[str] = Field(
        None,
        description="Identifies the purpose of this name. usual|official|temp|nickname|anonymous|old|maiden.",
    )
    text: Optional[str] = Field(
        None, description="Text representation of the full name, as it would normally be displayed."
    )
    family: Optional[str] = Field(None, description="Family name (often called 'surname').")
    given: Optional[List[str]] = Field(
        None, description="Given names (not always 'first'). Includes middle names — order matters."
    )
    prefix: Optional[List[str]] = Field(
        None, description="Parts that come before the name (e.g. Mr., Dr., titles)."
    )
    suffix: Optional[List[str]] = Field(
        None, description="Parts that come after the name (e.g. Jr., MD, qualifications)."
    )
    period: Optional[FHIRPeriod] = Field(
        None, description="The period during which this name was/is in use."
    )
