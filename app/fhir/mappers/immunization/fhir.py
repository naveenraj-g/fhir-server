"""ImmunizationModel row -> FHIR R4 Immunization. The only
read-side mapper.

The resource is stored whole in ImmunizationModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.immunization import ImmunizationModel


def to_fhir_immunization(immunization: ImmunizationModel) -> dict:
    return content_resource("Immunization", immunization.immunization_id, immunization)
