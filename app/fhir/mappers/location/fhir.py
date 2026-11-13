"""LocationModel row -> FHIR R4 Location. The only read-side mapper.

The resource is stored whole in LocationModel.content (see the model's
docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.location import LocationModel


def to_fhir_location(loc: LocationModel) -> dict:
    return content_resource("Location", loc.location_id, loc)
