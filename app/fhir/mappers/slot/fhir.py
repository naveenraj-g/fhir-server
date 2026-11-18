"""SlotModel row -> FHIR R4 Slot. The only
read-side mapper.

The resource is stored whole in SlotModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.slot import SlotModel


def to_fhir_slot(service: SlotModel) -> dict:
    return content_resource("Slot", service.slot_id, service)
