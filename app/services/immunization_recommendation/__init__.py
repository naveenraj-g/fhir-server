from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["ImmunizationRecommendationService"]


@trace_methods
class ImmunizationRecommendationService(_CoreMixin):
    """All ImmunizationRecommendation business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
