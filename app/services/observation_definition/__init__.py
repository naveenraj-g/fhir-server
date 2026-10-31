from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["ObservationDefinitionService"]


@trace_methods
class ObservationDefinitionService(_CoreMixin):
    """Orchestrates ObservationDefinition CRUD operations and data transformations."""
