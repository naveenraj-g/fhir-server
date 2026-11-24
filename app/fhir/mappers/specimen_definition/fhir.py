"""SpecimenDefinitionModel row -> FHIR R4 SpecimenDefinition. The only
read-side mapper.

The resource is stored whole in SpecimenDefinitionModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.specimen_definition import SpecimenDefinitionModel


def to_fhir_specimen_definition(specimen_definition: SpecimenDefinitionModel) -> dict:
    return content_resource(
        "SpecimenDefinition",
        specimen_definition.specimen_definition_id,
        specimen_definition,
    )
