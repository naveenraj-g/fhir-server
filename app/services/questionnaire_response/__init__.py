from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["QuestionnaireResponseService"]


@trace_methods
class QuestionnaireResponseService(_CoreMixin):
    """All QuestionnaireResponse business logic. __init__ (repository=...)
    is inherited from _CoreMixin."""
