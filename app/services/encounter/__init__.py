from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["EncounterService"]


@trace_methods
class EncounterService(_CoreMixin):
    """All Encounter business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
