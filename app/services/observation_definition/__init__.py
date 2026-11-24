from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["ObservationDefinitionService"]


@trace_methods
class ObservationDefinitionService(_CoreMixin):
    """All ObservationDefinition business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
