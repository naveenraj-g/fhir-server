from .address import PatientAddressInput
from .communication import PatientCommunicationInput
from .contact import PatientContactInput, PatientContactRelationshipInput
from .core import PatientCreateSchema, PatientPatchSchema
from .general_practitioner import PatientGeneralPractitionerInput
from .identifier import PatientIdentifierInput
from .link import PatientLinkInput
from .name import PatientNameInput
from .photo import PatientPhotoInput
from .telecom import PatientTelecomInput

__all__ = [
    "PatientAddressInput",
    "PatientCommunicationInput",
    "PatientContactInput",
    "PatientContactRelationshipInput",
    "PatientCreateSchema",
    "PatientGeneralPractitionerInput",
    "PatientIdentifierInput",
    "PatientLinkInput",
    "PatientNameInput",
    "PatientPatchSchema",
    "PatientPhotoInput",
    "PatientTelecomInput",
]
