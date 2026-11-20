"""ConditionModel row -> FHIR R4 Condition. The only
read-side mapper.

The resource is stored whole in ConditionModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.condition import ConditionModel


def to_fhir_condition(condition: ConditionModel) -> dict:
    return content_resource("Condition", condition.condition_id, condition)
