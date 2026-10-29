from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["DiagnosticReportService"]


@trace_methods
class DiagnosticReportService(_CoreMixin):
    """All DiagnosticReport business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
