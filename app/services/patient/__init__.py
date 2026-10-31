from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["PatientService"]


@trace_methods
class PatientService(_CoreMixin):
    """All Patient business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
