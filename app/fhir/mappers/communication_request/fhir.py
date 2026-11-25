"""CommunicationRequestModel row -> FHIR R4 CommunicationRequest. The only
read-side mapper.

The resource is stored whole in CommunicationRequestModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.communication_request import CommunicationRequestModel


def to_fhir_communication_request(
    communication_request: CommunicationRequestModel,
) -> dict:
    return content_resource(
        "CommunicationRequest",
        communication_request.communication_request_id,
        communication_request,
    )
