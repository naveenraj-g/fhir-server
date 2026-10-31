from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin

__all__ = ["ConsentRepository"]


@trace_methods
class ConsentRepository(_CoreMixin, _FullMixin, BaseRepository):
    """All Consent DB I/O."""
