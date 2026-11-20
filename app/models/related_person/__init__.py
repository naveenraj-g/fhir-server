from .address import RelatedPersonAddress
from .core import RelatedPersonModel, related_person_id_seq
from .identifier import RelatedPersonIdentifier
from .name import RelatedPersonName
from .relationship import RelatedPersonRelationship
from .telecom import RelatedPersonTelecom

__all__ = [
    "RelatedPersonAddress",
    "RelatedPersonIdentifier",
    "RelatedPersonModel",
    "RelatedPersonName",
    "RelatedPersonRelationship",
    "RelatedPersonTelecom",
    "related_person_id_seq",
]
