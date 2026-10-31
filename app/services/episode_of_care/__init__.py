from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["EpisodeOfCareService"]


@trace_methods
class EpisodeOfCareService(_CoreMixin):
    """Orchestrates EpisodeOfCare CRUD operations and data transformations."""
