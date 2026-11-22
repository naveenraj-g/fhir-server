"""CareTeamModel row -> FHIR R4 CareTeam. The only
read-side mapper.

The resource is stored whole in CareTeamModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.care_team import CareTeamModel


def to_fhir_care_team(care_team: CareTeamModel) -> dict:
    return content_resource("CareTeam", care_team.care_team_id, care_team)
