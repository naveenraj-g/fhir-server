"""ClinicalImpressionModel row -> FHIR R4 ClinicalImpression. The only
read-side mapper.

The resource is stored whole in ClinicalImpressionModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.clinical_impression import ClinicalImpressionModel


def to_fhir_clinical_impression(clinical_impression: ClinicalImpressionModel) -> dict:
    return content_resource(
        "ClinicalImpression",
        clinical_impression.clinical_impression_id,
        clinical_impression,
    )
