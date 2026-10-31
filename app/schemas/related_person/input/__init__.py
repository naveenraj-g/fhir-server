from app.schemas.related_person.input.address import RelatedPersonAddressInput
from app.schemas.related_person.input.communication import (
    RelatedPersonCommunicationInput,
)
from app.schemas.related_person.input.core import (
    RelatedPersonCreateSchema,
    RelatedPersonPatchSchema,
)
from app.schemas.related_person.input.identifier import (
    RelatedPersonIdentifierInput,
)
from app.schemas.related_person.input.name import RelatedPersonNameInput
from app.schemas.related_person.input.photo import RelatedPersonPhotoInput
from app.schemas.related_person.input.relationship import (
    RelatedPersonRelationshipInput,
)
from app.schemas.related_person.input.telecom import (
    RelatedPersonTelecomInput,
)

__all__ = [
    "RelatedPersonCreateSchema",
    "RelatedPersonPatchSchema",
    "RelatedPersonIdentifierInput",
    "RelatedPersonRelationshipInput",
    "RelatedPersonNameInput",
    "RelatedPersonTelecomInput",
    "RelatedPersonAddressInput",
    "RelatedPersonPhotoInput",
    "RelatedPersonCommunicationInput",
]
