from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["ConsentService"]


@trace_methods
class ConsentService(_CoreMixin):
    """All Consent business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
