from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["CommunicationRequestService"]


@trace_methods
class CommunicationRequestService(_CoreMixin):
    """All CommunicationRequest business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
