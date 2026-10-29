from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["ServiceRequestService"]


@trace_methods
class ServiceRequestService(_CoreMixin):
    """All ServiceRequest business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
