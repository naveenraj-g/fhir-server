from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["MedicationService"]


@trace_methods
class MedicationService(_CoreMixin):
    """All Medication business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
