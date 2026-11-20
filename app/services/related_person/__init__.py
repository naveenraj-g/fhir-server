from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["RelatedPersonService"]


@trace_methods
class RelatedPersonService(_CoreMixin):
    """All RelatedPerson business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
