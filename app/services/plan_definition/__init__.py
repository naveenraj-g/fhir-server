from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["PlanDefinitionService"]


@trace_methods
class PlanDefinitionService(_CoreMixin):
    """All PlanDefinition business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
