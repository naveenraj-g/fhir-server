from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .address import _AddressMixin
from .communication import _CommunicationMixin
from .contact import _ContactMixin
from .core import _CoreMixin
from .full import _FullMixin
from .general_practitioner import _GeneralPractitionerMixin
from .identifier import _IdentifierMixin
from .link import _LinkMixin
from .name import _NameMixin
from .photo import _PhotoMixin
from .telecom import _TelecomMixin

__all__ = ["PatientRepository"]


@trace_methods
class PatientRepository(
    _CoreMixin,
    _FullMixin,
    _NameMixin,
    _IdentifierMixin,
    _TelecomMixin,
    _AddressMixin,
    _PhotoMixin,
    _ContactMixin,
    _CommunicationMixin,
    _GeneralPractitionerMixin,
    _LinkMixin,
    BaseRepository,
):
    """
    session_factory/__init__ inherited from BaseRepository — see that class
    for the generic paginated-list execution _CoreMixin.list() delegates the
    sort/count/pagination mechanics to.

    Split into one mixin per sub-resource (see the sibling modules in this
    package) purely for file-size navigability — every method here behaves
    exactly as it did when this was a single 2276-line file.
    """
