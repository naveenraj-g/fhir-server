"""GroupModel row -> FHIR R4 Group. The only
read-side mapper.

The resource is stored whole in GroupModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.group import GroupModel


def to_fhir_group(group: GroupModel) -> dict:
    return content_resource("Group", group.group_id, group)
