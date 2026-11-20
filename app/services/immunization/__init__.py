from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["ImmunizationService"]


@trace_methods
class ImmunizationService(_CoreMixin):
    """All Immunization business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
