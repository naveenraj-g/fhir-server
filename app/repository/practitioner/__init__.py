from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin

__all__ = ["PractitionerRepository"]


@trace_methods
class PractitionerRepository(_CoreMixin, _FullMixin, BaseRepository):
    """All Practitioner DB I/O. Like Organization, Practitioner's create/patch
    always operate on the whole nested payload (see full.py) rather than a
    separate scalar-only vs. full split — see PractitionerCreateSchema's
    docstring. session_factory/__init__ and the generic paginated-list
    execution (`_execute_paginated`) are inherited from BaseRepository — see
    that class."""
