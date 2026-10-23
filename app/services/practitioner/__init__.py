from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["PractitionerService"]


@trace_methods
class PractitionerService(_CoreMixin):
    """All Practitioner business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
