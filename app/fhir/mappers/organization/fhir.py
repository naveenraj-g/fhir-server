"""OrganizationModel row -> FHIR R4 Organization. The only read-side mapper.

The resource is stored whole in OrganizationModel.content (see the model's
docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.organization import OrganizationModel


def to_fhir_organization(org: OrganizationModel) -> dict:
    return content_resource("Organization", org.organization_id, org)
