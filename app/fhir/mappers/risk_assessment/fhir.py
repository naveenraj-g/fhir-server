"""RiskAssessmentModel row -> FHIR R4 RiskAssessment. The only
read-side mapper.

The resource is stored whole in RiskAssessmentModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.risk_assessment import RiskAssessmentModel


def to_fhir_risk_assessment(risk_assessment: RiskAssessmentModel) -> dict:
    return content_resource("RiskAssessment", risk_assessment.risk_assessment_id, risk_assessment)
