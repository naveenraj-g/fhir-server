from .address import _AddressMixin
from .communication import _CommunicationMixin
from .core import _CoreMixin
from .identifier import _IdentifierMixin
from .name import _NameMixin
from .photo import _PhotoMixin
from .qualification import _QualificationMixin
from .telecom import _TelecomMixin

__all__ = ["PractitionerService"]


class PractitionerService(
    _CoreMixin,
    _NameMixin,
    _IdentifierMixin,
    _TelecomMixin,
    _AddressMixin,
    _PhotoMixin,
    _QualificationMixin,
    _CommunicationMixin,
):
    """Thin orchestration for Practitioner, composed from per-sub-resource mixins."""
