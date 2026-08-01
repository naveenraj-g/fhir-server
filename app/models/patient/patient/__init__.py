from .address import PatientAddress
from .communication import PatientCommunication
from .contact import PatientContact, PatientContactRelationship, PatientContactTelecom
from .core import PatientModel
from .general_practitioner import PatientGeneralPractitioner
from .identifier import PatientIdentifier
from .link import PatientLink
from .name import PatientName
from .photo import PatientPhoto
from .telecom import PatientTelecom

__all__ = [
    "PatientAddress",
    "PatientCommunication",
    "PatientContact",
    "PatientContactRelationship",
    "PatientContactTelecom",
    "PatientGeneralPractitioner",
    "PatientIdentifier",
    "PatientLink",
    "PatientModel",
    "PatientName",
    "PatientPhoto",
    "PatientTelecom",
]
