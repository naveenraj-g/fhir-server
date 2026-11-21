from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["RiskAssessmentService"]


@trace_methods
class RiskAssessmentService(_CoreMixin):
    """All RiskAssessment business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
