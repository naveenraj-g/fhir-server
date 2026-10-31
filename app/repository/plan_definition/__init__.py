from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin


class PlanDefinitionRepository(_CoreMixin, _FullMixin, BaseRepository):
    """PlanDefinition repository coordinating DB I/O."""

    pass


__all__ = ["PlanDefinitionRepository"]
