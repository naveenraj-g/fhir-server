"""CommunicationModel row -> FHIR R4 Communication. The only
read-side mapper.

The resource is stored whole in CommunicationModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.communication import CommunicationModel


def to_fhir_communication(communication: CommunicationModel) -> dict:
    return content_resource(
        "Communication", communication.communication_id, communication
    )
