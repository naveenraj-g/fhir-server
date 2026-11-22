"""CarePlanModel row -> FHIR R4 CarePlan. The only
read-side mapper.

The resource is stored whole in CarePlanModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.care_plan import CarePlanModel


def to_fhir_care_plan(care_plan: CarePlanModel) -> dict:
    return content_resource("CarePlan", care_plan.care_plan_id, care_plan)
