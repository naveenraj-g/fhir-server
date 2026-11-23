from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["EpisodeOfCareService"]


@trace_methods
class EpisodeOfCareService(_CoreMixin):
    """All EpisodeOfCare business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
