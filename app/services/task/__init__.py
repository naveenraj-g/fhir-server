from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["TaskService"]


@trace_methods
class TaskService(_CoreMixin):
    """All Task business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
