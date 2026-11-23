from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["DocumentReferenceService"]


@trace_methods
class DocumentReferenceService(_CoreMixin):
    """All DocumentReference business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
