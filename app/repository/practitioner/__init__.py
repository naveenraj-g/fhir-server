from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .address import _AddressMixin
from .communication import _CommunicationMixin
from .core import _CoreMixin
from .full import _FullMixin
from .identifier import _IdentifierMixin
from .name import _NameMixin
from .photo import _PhotoMixin
from .qualification import _QualificationMixin
from .telecom import _TelecomMixin

__all__ = ["PractitionerRepository"]


@trace_methods
class PractitionerRepository(
    _CoreMixin,
    _FullMixin,
    _NameMixin,
    _IdentifierMixin,
    _TelecomMixin,
    _AddressMixin,
    _PhotoMixin,
    _QualificationMixin,
    _CommunicationMixin,
    BaseRepository,
):
    """All Practitioner DB I/O, composed from per-sub-resource mixins.
    Every mixin method can call any other mixin's method or shared helper
    (e.g. `self._get_internal(...)`, `self.get_by_practitioner_id(...)`)
    regardless of which file defines it, since `self` at runtime is the
    fully-composed instance. session_factory/__init__ and the generic
    paginated-list execution (`_execute_paginated`) are inherited from
    BaseRepository — see that class."""
