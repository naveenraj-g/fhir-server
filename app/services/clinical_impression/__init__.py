from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["ClinicalImpressionService"]


@trace_methods
class ClinicalImpressionService(_CoreMixin):
    """All ClinicalImpression business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
