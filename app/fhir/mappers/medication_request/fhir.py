"""MedicationRequestModel row -> FHIR R4 MedicationRequest. The only
read-side mapper.

The resource is stored whole in MedicationRequestModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.medication_request import MedicationRequestModel


def to_fhir_medication_request(medication_request: MedicationRequestModel) -> dict:
    return content_resource(
        "MedicationRequest",
        medication_request.medication_request_id,
        medication_request,
    )
