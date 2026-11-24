from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["MedicationKnowledgeService"]


@trace_methods
class MedicationKnowledgeService(_CoreMixin):
    """All MedicationKnowledge business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
