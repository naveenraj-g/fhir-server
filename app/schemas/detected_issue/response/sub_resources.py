from pydantic import BaseModel, ConfigDict, Field

from .evidence import PlainDetectedIssueEvidence
from .identifier import PlainDetectedIssueIdentifier
from .mitigation import PlainDetectedIssueMitigation
from .reference import PlainDetectedIssueReference


class DetectedIssueIdentifierListItem(PlainDetectedIssueIdentifier):
    """Sub-resource list item for identifier."""


class DetectedIssueIdentifierListResponse(BaseModel):
    """Sub-resource list response for identifiers."""

    model_config = ConfigDict(extra="forbid")

    data: list[DetectedIssueIdentifierListItem] = Field(..., description="List of identifiers.")
    total: int = Field(..., description="Total count.")


class DetectedIssueImplicatedListItem(PlainDetectedIssueReference):
    """Sub-resource list item for implicated."""


class DetectedIssueImplicatedListResponse(BaseModel):
    """Sub-resource list response for implicated resources."""

    model_config = ConfigDict(extra="forbid")

    data: list[DetectedIssueImplicatedListItem] = Field(..., description="List of implicated references.")
    total: int = Field(..., description="Total count.")


class DetectedIssueEvidenceListItem(PlainDetectedIssueEvidence):
    """Sub-resource list item for evidence."""


class DetectedIssueEvidenceListResponse(BaseModel):
    """Sub-resource list response for evidence."""

    model_config = ConfigDict(extra="forbid")

    data: list[DetectedIssueEvidenceListItem] = Field(..., description="List of evidence items.")
    total: int = Field(..., description="Total count.")


class DetectedIssueMitigationListItem(PlainDetectedIssueMitigation):
    """Sub-resource list item for mitigation."""


class DetectedIssueMitigationListResponse(BaseModel):
    """Sub-resource list response for mitigations."""

    model_config = ConfigDict(extra="forbid")

    data: list[DetectedIssueMitigationListItem] = Field(..., description="List of mitigations.")
    total: int = Field(..., description="Total count.")
