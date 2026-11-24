from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["MeasureService"]


@trace_methods
class MeasureService(_CoreMixin):
    """All Measure business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
