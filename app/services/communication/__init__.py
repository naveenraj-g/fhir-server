from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["CommunicationService"]


@trace_methods
class CommunicationService(_CoreMixin):
    """All Communication business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
