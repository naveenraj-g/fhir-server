from .category import CommunicationCategoryInput
from .core import CommunicationCreateSchema, CommunicationPatchSchema
from .identifier import CommunicationIdentifierInput
from .note import CommunicationNoteInput
from .payload import CommunicationPayloadInput
from .reference import CommunicationReferenceInput

__all__ = [
    "CommunicationCreateSchema",
    "CommunicationPatchSchema",
    "CommunicationCategoryInput",
    "CommunicationIdentifierInput",
    "CommunicationNoteInput",
    "CommunicationPayloadInput",
    "CommunicationReferenceInput",
]
