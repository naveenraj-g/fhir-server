from pydantic import BaseModel, ConfigDict, Field

from .codeable_concept import PlainDetectedIssueCodeableConcept
from .reference import PlainDetectedIssueReference


class PlainDetectedIssueEvidence(BaseModel):
    """Plain snake_case response shape for DetectedIssue.evidence."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Internal DB ID of evidence.")
    code: list[PlainDetectedIssueCodeableConcept] | None = Field(
        None, description="Manifestation of the issue."
    )
    detail: list[PlainDetectedIssueReference] | None = Field(
        None, description="Supporting information / problem resource."
    )
