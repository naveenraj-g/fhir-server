from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["HealthcareServiceService"]


@trace_methods
class HealthcareServiceService(_CoreMixin):
    """All HealthcareService business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
