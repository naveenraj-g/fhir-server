from typing import Optional
from pydantic import BaseModel, Field


class FHIRPeriod(BaseModel):
    """FHIR R4 Period — a time range defined by start and end dates/times."""

    start: Optional[str] = Field(None, description="Starting ISO 8601 datetime, inclusive, of the period.")
    end: Optional[str] = Field(None, description="Ending ISO 8601 datetime, inclusive, of the period.")
