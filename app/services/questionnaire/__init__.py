from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["QuestionnaireService"]


@trace_methods
class QuestionnaireService(_CoreMixin):
    """All Questionnaire business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
