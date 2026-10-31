from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["ConsentService"]


@trace_methods
class ConsentService(_CoreMixin):
    """Orchestrates Consent CRUD operations and data transformations."""
