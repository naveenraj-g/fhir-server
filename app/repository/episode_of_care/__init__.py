from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin

__all__ = ["EpisodeOfCareRepository"]


@trace_methods
class EpisodeOfCareRepository(_CoreMixin, _FullMixin, BaseRepository):
    """All EpisodeOfCare DB I/O."""
