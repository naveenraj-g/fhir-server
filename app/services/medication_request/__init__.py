from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["MedicationRequestService"]


@trace_methods
class MedicationRequestService(_CoreMixin):
    """All MedicationRequest business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
