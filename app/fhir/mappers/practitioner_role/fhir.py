"""PractitionerRoleModel row -> FHIR R4 PractitionerRole. The only
read-side mapper.

The resource is stored whole in PractitionerRoleModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.practitioner_role import PractitionerRoleModel


def to_fhir_practitioner_role(service: PractitionerRoleModel) -> dict:
    return content_resource("PractitionerRole", service.practitioner_role_id, service)
