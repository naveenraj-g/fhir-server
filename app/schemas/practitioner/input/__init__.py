from app.schemas.datatypes import CodingInput

from .address import PractitionerAddressInput
from .communication import PractitionerCommunicationInput
from .core import PractitionerCreateSchema, PractitionerPatchSchema
from .identifier import PractitionerIdentifierInput
from .name import PractitionerNameInput
from .photo import PractitionerPhotoInput
from .qualification import (
    PractitionerQualificationIdentifierInput,
    PractitionerQualificationInput,
)
from .telecom import PractitionerTelecomInput

__all__ = [
    "CodingInput",
    "PractitionerAddressInput",
    "PractitionerCommunicationInput",
    "PractitionerCreateSchema",
    "PractitionerIdentifierInput",
    "PractitionerNameInput",
    "PractitionerPatchSchema",
    "PractitionerPhotoInput",
    "PractitionerQualificationIdentifierInput",
    "PractitionerQualificationInput",
    "PractitionerTelecomInput",
]
