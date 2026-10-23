from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.datatypes.period import FHIRPeriod


class FHIRContactPoint(BaseModel):
    """FHIR R4 ContactPoint — a contact detail (phone, email, etc.) for a person or organization."""

    system: Optional[str] = Field(
        None, description="Telecommunications form for this contact point. phone|fax|email|pager|url|sms|other."
    )
    value: Optional[str] = Field(
        None, description="The actual contact point details (e.g. a phone number or email address)."
    )
    use: Optional[str] = Field(None, description="Purpose of this contact point. home|work|temp|old|mobile.")
    rank: Optional[int] = Field(
        None, description="Preferred order of use among an individual's contact points — 1 indicates the most preferred."
    )
    period: Optional[FHIRPeriod] = Field(
        None, description="The period during which this contact point was/is in use."
    )
