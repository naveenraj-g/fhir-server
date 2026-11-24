"""GoalModel row -> FHIR R4 Goal. The only
read-side mapper.

The resource is stored whole in GoalModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.goal import GoalModel


def to_fhir_goal(goal: GoalModel) -> dict:
    return content_resource("Goal", goal.goal_id, goal)
