from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["ActivityDefinitionService"]


@trace_methods
class ActivityDefinitionService(_CoreMixin):
    """All ActivityDefinition business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
