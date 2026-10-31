from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["SpecimenService"]


@trace_methods
class SpecimenService(_CoreMixin):
    """All Specimen business logic."""
