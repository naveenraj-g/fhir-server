"""AllergyIntoleranceModel row -> FHIR R4 AllergyIntolerance. The only
read-side mapper.

The resource is stored whole in AllergyIntoleranceModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.allergy_intolerance import AllergyIntoleranceModel


def to_fhir_allergy_intolerance(allergy_intolerance: AllergyIntoleranceModel) -> dict:
    return content_resource("AllergyIntolerance", allergy_intolerance.allergy_intolerance_id, allergy_intolerance)
