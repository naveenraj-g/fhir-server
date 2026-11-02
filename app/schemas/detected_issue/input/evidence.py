from pydantic import BaseModel, ConfigDict, Field

from .codeable_concept import DetectedIssueCodeableConceptInput
from .reference import DetectedIssueEvidenceDetailInput


class DetectedIssueEvidenceInput(BaseModel):
    """DetectedIssue.evidence input shape."""

    model_config = ConfigDict(extra="forbid")

    code: list[DetectedIssueCodeableConceptInput] | None = Field(
        None, description="Manifestation of the issue."
    )
    detail: list[DetectedIssueEvidenceDetailInput] | None = Field(
        None, description="Supporting information / problem resource."
    )
