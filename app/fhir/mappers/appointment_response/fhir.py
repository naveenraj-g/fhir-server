"""AppointmentResponseModel row -> FHIR R4 AppointmentResponse. The only
read-side mapper.

The resource is stored whole in AppointmentResponseModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.appointment_response import AppointmentResponseModel


def to_fhir_appointment_response(
    appointment_response: AppointmentResponseModel,
) -> dict:
    return content_resource(
        "AppointmentResponse",
        appointment_response.appointment_response_id,
        appointment_response,
    )
