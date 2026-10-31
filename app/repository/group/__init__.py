from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin

__all__ = ["GroupRepository"]


@trace_methods
class GroupRepository(_CoreMixin, _FullMixin, BaseRepository):
    """All Group DB I/O."""
