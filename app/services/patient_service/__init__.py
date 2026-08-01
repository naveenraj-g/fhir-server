from .address import _AddressMixin
from .communication import _CommunicationMixin
from .contact import _ContactMixin
from .core import _CoreMixin
from .general_practitioner import _GeneralPractitionerMixin
from .identifier import _IdentifierMixin
from .link import _LinkMixin
from .name import _NameMixin
from .photo import _PhotoMixin
from .telecom import _TelecomMixin

__all__ = ["PatientService"]


class PatientService(
    _CoreMixin,
    _NameMixin,
    _IdentifierMixin,
    _TelecomMixin,
    _AddressMixin,
    _PhotoMixin,
    _ContactMixin,
    _CommunicationMixin,
    _GeneralPractitionerMixin,
    _LinkMixin,
):
    """
    Thin orchestration layer between the router and PatientRepository.

    Every method here is a direct pass-through to the repository — no
    business logic lives in this class. It exists to give the router a
    stable interface that doesn't depend on repository internals, and to own
    the four formatter methods (_to_fhir/_to_plain/_to_fhir_core/_to_plain_core,
    on _CoreMixin) so the router never has to import the mapper functions
    directly for the main Patient representation (it still imports them
    directly for the sub-resource list routes — see app/routers/patient/).

    __init__(self, repository) lives on _CoreMixin. Split into one mixin per
    sub-resource (see the sibling modules in this package) purely for
    file-size navigability — every method here behaves exactly as it did
    when this was a single 715-line file.
    """
