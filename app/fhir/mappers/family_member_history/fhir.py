"""FamilyMemberHistoryModel row -> FHIR R4 FamilyMemberHistory. The only
read-side mapper.

The resource is stored whole in FamilyMemberHistoryModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.family_member_history import FamilyMemberHistoryModel


def to_fhir_family_member_history(
    family_member_history: FamilyMemberHistoryModel,
) -> dict:
    return content_resource(
        "FamilyMemberHistory",
        family_member_history.family_member_history_id,
        family_member_history,
    )
