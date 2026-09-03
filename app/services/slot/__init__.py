from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["SlotService"]


@trace_methods
class SlotService(_CoreMixin):
    """All Slot business logic. __init__ (repository=...) is inherited from
    _CoreMixin."""
