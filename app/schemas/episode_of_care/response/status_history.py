from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.datatypes import AuditFields, FHIRPeriod


class FHIRStatusHistory(BaseModel):
    """FHIR representation of EpisodeOfCare.statusHistory."""

    model_config = ConfigDict(extra="forbid")

    status: str
    period: FHIRPeriod | None = None


class PlainEpisodeOfCareStatusHistory(AuditFields, BaseModel):
    """Plain response representation of EpisodeOfCare statusHistory."""

    model_config = ConfigDict(extra="forbid")

    id: int
    status: str
    period_start: datetime | None = None
    period_end: datetime | None = None
