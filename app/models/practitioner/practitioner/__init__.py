from .address import PractitionerAddress
from .communication import PractitionerCommunication
from .core import PractitionerModel
from .identifier import PractitionerIdentifier
from .name import PractitionerName
from .photo import PractitionerPhoto
from .qualification import PractitionerQualification, PractitionerQualificationIdentifier
from .telecom import PractitionerTelecom

__all__ = [
    "PractitionerAddress",
    "PractitionerCommunication",
    "PractitionerIdentifier",
    "PractitionerModel",
    "PractitionerName",
    "PractitionerPhoto",
    "PractitionerQualification",
    "PractitionerQualificationIdentifier",
    "PractitionerTelecom",
]
