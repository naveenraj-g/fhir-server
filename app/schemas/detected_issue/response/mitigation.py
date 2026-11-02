from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .codeable_concept import PlainDetectedIssueCodeableConcept
from .reference import PlainDetectedIssueReference


class PlainDetectedIssueMitigation(BaseModel):
    """Plain snake_case response shape for DetectedIssue.mitigation."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Internal DB ID of mitigation.")
    action: PlainDetectedIssueCodeableConcept = Field(
        ..., description="What mitigation was taken."
    )
    date: datetime | None = Field(None, description="Date committed.")
    author: PlainDetectedIssueReference | None = Field(
        None, description="Who committed the mitigation."
    )
