from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin

__all__ = ["ConditionRepository"]


@trace_methods
class ConditionRepository(_CoreMixin, _FullMixin, BaseRepository):
    """All Condition DB I/O."""
