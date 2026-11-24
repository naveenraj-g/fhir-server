from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["FlagService"]


@trace_methods
class FlagService(_CoreMixin):
    """All Flag business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
