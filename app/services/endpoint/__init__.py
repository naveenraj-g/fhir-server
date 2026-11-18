from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["EndpointService"]


@trace_methods
class EndpointService(_CoreMixin):
    """All Endpoint business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
