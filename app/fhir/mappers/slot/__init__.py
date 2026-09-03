from app.fhir.mappers.slot.fhir import (
    fhir_slot_appointment_type,
    fhir_slot_identifier,
    fhir_slot_schedule,
    fhir_slot_service_category,
    fhir_slot_service_type,
    fhir_slot_specialty,
    to_fhir_slot,
)
from app.fhir.mappers.slot.plain import (
    plain_slot_identifier,
    plain_slot_service_category,
    plain_slot_service_type,
    plain_slot_specialty,
    to_plain_slot,
)

__all__ = [
    "fhir_slot_appointment_type",
    "fhir_slot_identifier",
    "fhir_slot_schedule",
    "fhir_slot_service_category",
    "fhir_slot_service_type",
    "fhir_slot_specialty",
    "plain_slot_identifier",
    "plain_slot_service_category",
    "plain_slot_service_type",
    "plain_slot_specialty",
    "to_fhir_slot",
    "to_plain_slot",
]
