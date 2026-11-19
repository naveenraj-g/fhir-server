"""AppointmentModel row -> FHIR R4 Appointment. The only
read-side mapper.

The resource is stored whole in AppointmentModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.appointment import AppointmentModel


def to_fhir_appointment(appointment: AppointmentModel) -> dict:
    return content_resource("Appointment", appointment.appointment_id, appointment)
