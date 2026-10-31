from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin

__all__ = ["DocumentReferenceRepository"]


@trace_methods
class DocumentReferenceRepository(_CoreMixin, _FullMixin, BaseRepository):
    """All DocumentReference DB I/O."""
