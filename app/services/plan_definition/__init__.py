from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["PlanDefinitionService"]


@trace_methods
class PlanDefinitionService(_CoreMixin):
    """Orchestrates PlanDefinition CRUD operations and data transformations."""
