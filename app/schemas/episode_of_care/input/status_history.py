from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import EpisodeOfCareStatus


class EpisodeOfCareStatusHistoryInput(BaseModel):
    """Input representation of a statusHistory entry for EpisodeOfCare."""

    model_config = ConfigDict(extra="forbid")

    status: EpisodeOfCareStatus = Field(
        ..., description="planned | waitlist | active | onhold | finished | cancelled | entered-in-error"
    )
    period_start: datetime | None = Field(None, description="Starting time with status.")
    period_end: datetime | None = Field(None, description="Ending time with status.")
