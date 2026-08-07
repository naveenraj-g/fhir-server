from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin

__all__ = ["OrganizationRepository"]


@trace_methods
class OrganizationRepository(_CoreMixin, _FullMixin, BaseRepository):
    """All Organization DB I/O. Unlike Patient/Practitioner, Organization has
    no standalone sub-resource endpoints (it's a set-once-rarely-edited
    resource — see OrganizationCreateSchema's docstring), so create/patch
    always operate on the whole nested payload (see full.py) and there are no
    per-sub-resource mixins. session_factory/__init__ and the generic
    paginated-list execution (`_execute_paginated`) are inherited from
    BaseRepository — see that class."""
