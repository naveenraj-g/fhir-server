from .address import AddressCreate, AddressPatch
from .communication import CommunicationCreate, CommunicationPatch
from .contact import (
    ContactCreate,
    ContactPatch,
    ContactRelationshipCreate,
    ContactTelecomCreate,
)
from .core import (
    PatientCreateSchema,
    PatientFullCreateSchema,
    PatientFullPatchSchema,
    PatientPatchSchema,
)
from .general_practitioner import GeneralPractitionerCreate, GeneralPractitionerPatch
from .identifier import IdentifierCreate, IdentifierPatch
from .link import LinkCreate, LinkPatch
from .name import NameCreate, NamePatch
from .photo import PhotoCreate, PhotoPatch
from .telecom import TelecomCreate, TelecomPatch

__all__ = [
    "AddressCreate",
    "AddressPatch",
    "CommunicationCreate",
    "CommunicationPatch",
    "ContactCreate",
    "ContactPatch",
    "ContactRelationshipCreate",
    "ContactTelecomCreate",
    "GeneralPractitionerCreate",
    "GeneralPractitionerPatch",
    "IdentifierCreate",
    "IdentifierPatch",
    "LinkCreate",
    "LinkPatch",
    "NameCreate",
    "NamePatch",
    "PatientCreateSchema",
    "PatientFullCreateSchema",
    "PatientFullPatchSchema",
    "PatientPatchSchema",
    "PhotoCreate",
    "PhotoPatch",
    "TelecomCreate",
    "TelecomPatch",
]
