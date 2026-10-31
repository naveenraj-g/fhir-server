from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin


class ActivityDefinitionRepository(_CoreMixin, _FullMixin, BaseRepository):
    """ActivityDefinition repository coordinating DB I/O."""

    pass


__all__ = ["ActivityDefinitionRepository"]
