from app.fhir.mappers.practitioner.fhir import (
    to_fhir_practitioner, fhir_qualification, fhir_practitioner_communication,
    fhir_identifier,
)
from app.fhir.mappers.practitioner.plain import (
    to_plain_practitioner, plain_qualification, plain_practitioner_communication,
    plain_identifier, plain_name, plain_telecom, plain_address, plain_photo,
)

__all__ = [
    "to_fhir_practitioner", "fhir_qualification", "fhir_practitioner_communication",
    "fhir_identifier",
    "to_plain_practitioner", "plain_qualification", "plain_practitioner_communication",
    "plain_identifier", "plain_name", "plain_telecom", "plain_address", "plain_photo",
]
