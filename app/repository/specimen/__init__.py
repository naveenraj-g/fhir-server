from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin

__all__ = ["SpecimenRepository"]


@trace_methods
class SpecimenRepository(_CoreMixin, _FullMixin, BaseRepository):
    """All Specimen DB I/O."""
