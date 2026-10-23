from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["ScheduleService"]


@trace_methods
class ScheduleService(_CoreMixin):
    """All Schedule business logic. __init__ (repository=...) is inherited
    from _CoreMixin."""
