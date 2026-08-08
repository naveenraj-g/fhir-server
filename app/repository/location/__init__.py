from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin

__all__ = ["LocationRepository"]


@trace_methods
class LocationRepository(_CoreMixin, _FullMixin, BaseRepository):
    """All Location DB I/O. Like Organization (and unlike Patient/Practitioner)
    there are no standalone sub-resource write endpoints, so create/patch
    always operate on the whole nested payload (see full.py) and there are no
    per-sub-resource mixins. session_factory/__init__ and the generic
    paginated-list execution (`_execute_paginated`) are inherited from
    BaseRepository — see that class."""
