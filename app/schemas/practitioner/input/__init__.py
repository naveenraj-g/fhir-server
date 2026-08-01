from .address import PractitionerAddressCreate, PractitionerAddressPatch
from .communication import (
    PractitionerCommunicationCreate,
    PractitionerCommunicationPatch,
)
from .core import (
    PractitionerCreateSchema,
    PractitionerFullCreateSchema,
    PractitionerFullPatchSchema,
    PractitionerPatchSchema,
)
from .identifier import PractitionerIdentifierCreate, PractitionerIdentifierPatch
from .name import PractitionerNameCreate, PractitionerNamePatch
from .photo import PractitionerPhotoCreate, PractitionerPhotoPatch
from .qualification import (
    PractitionerQualificationCreate,
    PractitionerQualificationPatch,
    QualificationIdentifierCreate,
    QualificationIdentifierPatch,
)
from .telecom import PractitionerTelecomCreate, PractitionerTelecomPatch

__all__ = [
    "PractitionerCreateSchema",
    "PractitionerPatchSchema",
    "PractitionerFullCreateSchema",
    "PractitionerFullPatchSchema",
    "PractitionerNameCreate",
    "PractitionerNamePatch",
    "PractitionerIdentifierCreate",
    "PractitionerIdentifierPatch",
    "PractitionerTelecomCreate",
    "PractitionerTelecomPatch",
    "PractitionerAddressCreate",
    "PractitionerAddressPatch",
    "PractitionerPhotoCreate",
    "PractitionerPhotoPatch",
    "QualificationIdentifierCreate",
    "QualificationIdentifierPatch",
    "PractitionerQualificationCreate",
    "PractitionerQualificationPatch",
    "PractitionerCommunicationCreate",
    "PractitionerCommunicationPatch",
]
