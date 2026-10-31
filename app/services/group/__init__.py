from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["GroupService"]


@trace_methods
class GroupService(_CoreMixin):
    """Orchestrates Group CRUD operations and data transformations."""
