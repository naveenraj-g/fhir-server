"""ImmunizationEvaluationModel row -> FHIR R4 ImmunizationEvaluation. The only
read-side mapper.

The resource is stored whole in ImmunizationEvaluationModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.immunization_evaluation import ImmunizationEvaluationModel


def to_fhir_immunization_evaluation(immunization_evaluation: ImmunizationEvaluationModel) -> dict:
    return content_resource("ImmunizationEvaluation", immunization_evaluation.immunization_evaluation_id, immunization_evaluation)
