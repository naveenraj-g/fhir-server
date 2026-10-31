from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["CarePlanService"]


@trace_methods
class CarePlanService(_CoreMixin):
    """Orchestrates CarePlan CRUD operations and data transformations."""
