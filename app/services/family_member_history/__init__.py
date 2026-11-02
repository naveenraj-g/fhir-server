from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["FamilyMemberHistoryService"]


@trace_methods
class FamilyMemberHistoryService(_CoreMixin):
    """Orchestrates FamilyMemberHistory CRUD operations and data transformations."""
