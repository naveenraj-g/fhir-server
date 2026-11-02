from app.repository.base import BaseRepository
from app.repository.detected_issue.core import _CoreMixin
from app.repository.detected_issue.full import _FullMixin


class DetectedIssueRepository(BaseRepository, _CoreMixin, _FullMixin):
    """Repository managing DetectedIssue persistence and queries."""


__all__ = ["DetectedIssueRepository"]
