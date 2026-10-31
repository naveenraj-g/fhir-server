from pydantic import BaseModel, ConfigDict, Field


class _PlainReferenceResponse(BaseModel):
    """Shared plain reference response."""

    model_config = ConfigDict(extra="allow")
    reference: str | None = Field(None, description="FHIR reference string.")
    id: int | None = Field(None, description="Target resource public sequence ID.")
    type: str | None = Field(None, description="Target resource type.")
    display: str | None = Field(None, description="Plain text display.")


class PlainConditionSubject(_PlainReferenceResponse):
    """Condition.subject reference plain response."""


class PlainConditionEncounter(_PlainReferenceResponse):
    """Condition.encounter reference plain response."""


class PlainConditionRecorder(_PlainReferenceResponse):
    """Condition.recorder reference plain response."""


class PlainConditionAsserter(_PlainReferenceResponse):
    """Condition.asserter reference plain response."""


class PlainConditionStageAssessment(_PlainReferenceResponse):
    """Condition.stage.assessment reference plain response."""


class PlainConditionEvidenceDetail(_PlainReferenceResponse):
    """Condition.evidence.detail reference plain response."""
