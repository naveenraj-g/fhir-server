from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["MedicationAdministrationService"]


@trace_methods
class MedicationAdministrationService(_CoreMixin):
    """All MedicationAdministration business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
