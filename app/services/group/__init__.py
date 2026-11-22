from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["GroupService"]


@trace_methods
class GroupService(_CoreMixin):
    """All Group business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
