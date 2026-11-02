from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .codeable_concept import DetectedIssueCodeableConceptInput
from .reference import DetectedIssueMitigationAuthorInput


class DetectedIssueMitigationInput(BaseModel):
    """DetectedIssue.mitigation input shape."""

    model_config = ConfigDict(extra="forbid")

    action: DetectedIssueCodeableConceptInput = Field(
        ..., description="What mitigation was taken (1..1)."
    )
    date: datetime | None = Field(None, description="Date committed.")
    author: DetectedIssueMitigationAuthorInput | None = Field(
        None, description="Who committed the mitigation."
    )
