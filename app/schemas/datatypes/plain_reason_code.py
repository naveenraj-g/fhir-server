from typing import Optional
from pydantic import BaseModel, Field


class PlainReasonCode(BaseModel):
    """Plain-JSON CodeableConcept used for reason-code style fields."""

    coding_system: Optional[str] = Field(None, description="Coding system that defines this reason code.")
    coding_code: Optional[str] = Field(None, description="Code for the reason.")
    coding_display: Optional[str] = Field(None, description="Human-readable display for the reason code.")
    text: Optional[str] = Field(None, description="Plain-text rendering of the reason CodeableConcept.")
