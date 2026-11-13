"""
FHIR R4-shaped *input* datatypes — the write-side building blocks for any
resource whose create/patch request body is genuine FHIR JSON (camelCase,
nested datatypes) rather than this project's older flattened snake_case
input shape.

Organization is the first (pilot) resource built on these. Such a resource
needs no `payload.py` mapper: the request body *is* the FHIR resource, so it
is validated as sent (app.fhir.input_payload) and, for a resource stored
Medplum-style, saved verbatim in its `content` JSONB column.

These models are not the source of what gets stored — the validated raw
body is. They exist to document the request shape in OpenAPI (the MCP
contract), to type-check the common elements early, and to type every
required-binding code as its real enum. Any other valid FHIR R4 element
(element-level `id`/`extension`, `modifierExtension`, ...) is accepted by
FhirInputModel's `extra="ignore"` and still stored, since `content` keeps
the whole validated body. Whether the body is valid FHIR at all is decided
by base R4 validation, so a key that isn't FHIR is a 422.
"""

from app.schemas.fhir_input.address import FhirAddressInput
from app.schemas.fhir_input.base import FhirInputModel
from app.schemas.fhir_input.codeable_concept import FhirCodeableConceptInput
from app.schemas.fhir_input.coding import FhirCodingInput
from app.schemas.fhir_input.contact_point import FhirContactPointInput
from app.schemas.fhir_input.human_name import FhirHumanNameInput
from app.schemas.fhir_input.identifier import FhirIdentifierInput
from app.schemas.fhir_input.period import FhirPeriodInput
from app.schemas.fhir_input.reference import FhirReferenceInput

__all__ = [
    "FhirAddressInput",
    "FhirCodeableConceptInput",
    "FhirCodingInput",
    "FhirContactPointInput",
    "FhirHumanNameInput",
    "FhirIdentifierInput",
    "FhirInputModel",
    "FhirPeriodInput",
    "FhirReferenceInput",
]
