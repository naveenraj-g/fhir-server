"""DetectedIssueModel row -> FHIR R4 DetectedIssue. The only
read-side mapper.

The resource is stored whole in DetectedIssueModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.detected_issue import DetectedIssueModel


def to_fhir_detected_issue(detected_issue: DetectedIssueModel) -> dict:
    return content_resource(
        "DetectedIssue", detected_issue.detected_issue_id, detected_issue
    )
