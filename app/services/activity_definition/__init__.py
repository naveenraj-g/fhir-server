from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["ActivityDefinitionService"]


@trace_methods
class ActivityDefinitionService(_CoreMixin):
    """Orchestrates ActivityDefinition CRUD operations and data transformations."""
