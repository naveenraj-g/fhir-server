from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["DetectedIssueService"]


@trace_methods
class DetectedIssueService(_CoreMixin):
    """All DetectedIssue business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
