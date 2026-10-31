from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes.period import FHIRPeriod
from app.schemas.datatypes.reference import FHIRReference
from app.schemas.task.response.reference import PlainTaskReference


class FHIRTaskRestriction(BaseModel):
    """FHIR R4 Task.restriction element."""

    repetitions: int | None = None
    period: FHIRPeriod | None = None
    recipient: list[FHIRReference] | None = None


class PlainTaskRestriction(BaseModel):
    """Plain snake_case serialization of Task restriction."""

    model_config = ConfigDict(extra="allow")

    repetitions: int | None = None
    period_start: str | None = None
    period_end: str | None = None
    recipients: list[PlainTaskReference] | None = None
