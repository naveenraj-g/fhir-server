from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["MedicationStatementService"]


@trace_methods
class MedicationStatementService(_CoreMixin):
    """All MedicationStatement business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
