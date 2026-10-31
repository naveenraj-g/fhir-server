from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["AllergyIntoleranceService"]


@trace_methods
class AllergyIntoleranceService(_CoreMixin):
    """Orchestrates AllergyIntolerance CRUD operations and data transformations."""
