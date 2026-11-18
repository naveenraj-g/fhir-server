from .communication import PatientCommunicationInput
from .contact import PatientContactInput
from .core import PatientCreateSchema, PatientPatchSchema
from .link import PatientLinkInput
from .user_link import PatientUserLinkInput

__all__ = [
    "PatientCommunicationInput",
    "PatientContactInput",
    "PatientCreateSchema",
    "PatientLinkInput",
    "PatientPatchSchema",
    "PatientUserLinkInput",
]
