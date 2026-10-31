from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["DocumentReferenceService"]


@trace_methods
class DocumentReferenceService(_CoreMixin):
    """Orchestrates DocumentReference business logic."""
