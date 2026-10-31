from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRPeriod, FHIRReference


class PlainGroupMember(BaseModel):
    """Plain response schema for Group member."""

    model_config = ConfigDict(extra="ignore")

    id: int = Field(..., description="Internal DB ID.")
    entity: str = Field(..., description="Member entity reference string.")
    entity_display: str | None = Field(None, description="Display text for entity.")
    period_start: datetime | None = Field(None, description="Membership period start.")
    period_end: datetime | None = Field(None, description="Membership period end.")
    inactive: bool | None = Field(None, description="Whether member is inactive.")


class FHIRGroupMember(BaseModel):
    """FHIR R4 Group member element."""

    model_config = ConfigDict(extra="allow")

    entity: FHIRReference = Field(..., description="Reference to the group member.")
    period: FHIRPeriod | None = None
    inactive: bool | None = None
