from app.models.patient.address import PatientAddress
from app.models.patient.communication import (
    PatientCommunication,
    PatientCommunicationLanguageCoding,
)
from app.models.patient.contact import (
    PatientContact,
    PatientContactRelationship,
    PatientContactRelationshipCoding,
    PatientContactTelecom,
)
from app.models.patient.core import PatientModel, patient_id_seq
from app.models.patient.enums import (
    PatientGeneralPractitionerReferenceType,
    PatientLinkOtherType,
    PatientLinkType,
)
from app.models.patient.general_practitioner import PatientGeneralPractitioner
from app.models.patient.identifier import (
    PatientIdentifier,
    PatientIdentifierTypeCoding,
)
from app.models.patient.link import PatientLink
from app.models.patient.marital_status import PatientMaritalStatusCoding
from app.models.patient.name import PatientName
from app.models.patient.photo import PatientPhoto
from app.models.patient.telecom import PatientTelecom

__all__ = [
    "PatientAddress",
    "PatientCommunication",
    "PatientCommunicationLanguageCoding",
    "PatientContact",
    "PatientContactRelationship",
    "PatientContactRelationshipCoding",
    "PatientContactTelecom",
    "PatientGeneralPractitioner",
    "PatientGeneralPractitionerReferenceType",
    "PatientIdentifier",
    "PatientIdentifierTypeCoding",
    "PatientLink",
    "PatientLinkOtherType",
    "PatientLinkType",
    "PatientMaritalStatusCoding",
    "PatientModel",
    "PatientName",
    "PatientPhoto",
    "PatientTelecom",
    "patient_id_seq",
]
