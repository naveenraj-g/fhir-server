from .address import PlainPatientAddress
from .communication import FHIRPatientCommunication, PlainPatientCommunication
from .contact import (
    FHIRPatientContact,
    PlainPatientContact,
    PlainPatientContactRelationship,
)
from .core import (
    FHIRPatientBundle,
    FHIRPatientBundleEntry,
    FHIRPatientSchema,
    PaginatedPatientResponse,
    PlainPatientResponse,
)
from .general_practitioner import PlainPatientGeneralPractitioner
from .identifier import PlainPatientIdentifier
from .link import FHIRPatientLink, PlainPatientLink
from .name import PlainPatientName
from .photo import PlainPatientPhoto
from .telecom import PlainPatientTelecom

__all__ = [
    "FHIRPatientBundle",
    "FHIRPatientBundleEntry",
    "FHIRPatientCommunication",
    "FHIRPatientContact",
    "FHIRPatientLink",
    "FHIRPatientSchema",
    "PaginatedPatientResponse",
    "PlainPatientAddress",
    "PlainPatientCommunication",
    "PlainPatientContact",
    "PlainPatientContactRelationship",
    "PlainPatientGeneralPractitioner",
    "PlainPatientIdentifier",
    "PlainPatientLink",
    "PlainPatientName",
    "PlainPatientPhoto",
    "PlainPatientResponse",
    "PlainPatientTelecom",
]
