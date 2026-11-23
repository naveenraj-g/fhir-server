from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["MedicationDispenseService"]


@trace_methods
class MedicationDispenseService(_CoreMixin):
    """All MedicationDispense business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
