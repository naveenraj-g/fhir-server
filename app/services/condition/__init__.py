from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["ConditionService"]


@trace_methods
class ConditionService(_CoreMixin):
    """All Condition business logic."""
