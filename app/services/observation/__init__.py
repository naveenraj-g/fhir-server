from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["ObservationService"]


@trace_methods
class ObservationService(_CoreMixin):
    """All Observation business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
