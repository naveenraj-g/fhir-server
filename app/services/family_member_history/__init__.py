from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["FamilyMemberHistoryService"]


@trace_methods
class FamilyMemberHistoryService(_CoreMixin):
    """All FamilyMemberHistory business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
