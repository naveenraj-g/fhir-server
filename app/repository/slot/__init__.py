from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin

__all__ = ["SlotRepository"]


@trace_methods
class SlotRepository(_CoreMixin, _FullMixin, BaseRepository):
    """All Slot DB I/O. Like Schedule, Slot has no standalone sub-resource
    endpoints (create/patch always operate on the whole nested payload — see
    full.py), so there are no per-sub-resource mixins beyond
    _CoreMixin/_FullMixin. session_factory/__init__ and the generic
    paginated-list execution (`_execute_paginated`) are inherited from
    BaseRepository — see that class."""
