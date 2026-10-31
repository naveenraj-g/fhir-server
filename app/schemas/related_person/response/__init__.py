from app.schemas.related_person.response.address import PlainRelatedPersonAddress
from app.schemas.related_person.response.communication import (
    FHIRRelatedPersonCommunication,
    PlainRelatedPersonCommunication,
)
from app.schemas.related_person.response.core import (
    FHIRRelatedPersonBundle,
    FHIRRelatedPersonBundleEntry,
    FHIRRelatedPersonSchema,
    PaginatedRelatedPersonResponse,
    PlainRelatedPersonResponse,
)
from app.schemas.related_person.response.identifier import (
    PlainRelatedPersonIdentifier,
)
from app.schemas.related_person.response.name import PlainRelatedPersonName
from app.schemas.related_person.response.photo import PlainRelatedPersonPhoto
from app.schemas.related_person.response.relationship import (
    PlainRelatedPersonRelationship,
)
from app.schemas.related_person.response.telecom import PlainRelatedPersonTelecom

__all__ = [
    "FHIRRelatedPersonSchema",
    "FHIRRelatedPersonBundleEntry",
    "FHIRRelatedPersonBundle",
    "PlainRelatedPersonResponse",
    "PaginatedRelatedPersonResponse",
    "PlainRelatedPersonIdentifier",
    "PlainRelatedPersonRelationship",
    "PlainRelatedPersonName",
    "PlainRelatedPersonTelecom",
    "PlainRelatedPersonAddress",
    "PlainRelatedPersonPhoto",
    "FHIRRelatedPersonCommunication",
    "PlainRelatedPersonCommunication",
]
