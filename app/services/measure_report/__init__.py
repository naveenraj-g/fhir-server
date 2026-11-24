from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["MeasureReportService"]


@trace_methods
class MeasureReportService(_CoreMixin):
    """All MeasureReport business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
