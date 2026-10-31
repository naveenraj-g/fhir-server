from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin

__all__ = ["ProcedureRepository"]


@trace_methods
class ProcedureRepository(_CoreMixin, _FullMixin, BaseRepository):
    """All Procedure DB I/O."""
