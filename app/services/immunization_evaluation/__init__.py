from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["ImmunizationEvaluationService"]


@trace_methods
class ImmunizationEvaluationService(_CoreMixin):
    """All ImmunizationEvaluation business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
