from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin

__all__ = ["PatientRepository"]


@trace_methods
class PatientRepository(_CoreMixin, _FullMixin, BaseRepository):
    """All Patient DB I/O. Like Organization, Patient's create/patch
    always operate on the whole nested payload (see full.py) rather than a
    separate scalar-only vs. full split — see PatientCreateSchema's
    docstring. session_factory/__init__ and the generic paginated-list
    execution (`_execute_paginated`) are inherited from BaseRepository — see
    that class."""
