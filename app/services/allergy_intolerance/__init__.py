from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["AllergyIntoleranceService"]


@trace_methods
class AllergyIntoleranceService(_CoreMixin):
    """All AllergyIntolerance business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
