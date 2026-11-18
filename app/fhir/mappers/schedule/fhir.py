"""ScheduleModel row -> FHIR R4 Schedule. The only
read-side mapper.

The resource is stored whole in ScheduleModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.schedule import ScheduleModel


def to_fhir_schedule(service: ScheduleModel) -> dict:
    return content_resource("Schedule", service.schedule_id, service)
