from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin

__all__ = ["PatientRepository"]


@trace_methods
class PatientRepository(_CoreMixin, _FullMixin, BaseRepository):
    """All Patient DB I/O. Atomic nested-write orchestrators (create_full, patch_full)
    live in full.py; single-row lookups, existence checks, list(), get_me(), and delete()
    live in core.py; eager-loading and shared reference helpers live in _shared.py.
    """
