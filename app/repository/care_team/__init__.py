from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin

__all__ = ["CareTeamRepository"]


@trace_methods
class CareTeamRepository(_CoreMixin, _FullMixin, BaseRepository):
    """All CareTeam DB I/O."""
