from app.fhir.datatypes import merge_patch_fragment
from .fhir import to_fhir_communication_request
from .payload import (
    patch_fragment_to_fhir_communication_request,
    payload_to_fhir_communication_request,
)
from .plain import to_plain_communication_request

__all__ = [
    "merge_patch_fragment",
    "patch_fragment_to_fhir_communication_request",
    "payload_to_fhir_communication_request",
    "to_fhir_communication_request",
    "to_plain_communication_request",
]
