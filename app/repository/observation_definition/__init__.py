from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin


class ObservationDefinitionRepository(_CoreMixin, _FullMixin, BaseRepository):
    """ObservationDefinition repository coordinating DB I/O."""

    pass


__all__ = ["ObservationDefinitionRepository"]
