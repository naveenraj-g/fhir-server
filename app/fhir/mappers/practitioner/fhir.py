"""PractitionerModel row -> FHIR R4 Practitioner. The only read-side mapper.

The resource is stored whole in PractitionerModel.content (see the model's
docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.practitioner import PractitionerModel


def to_fhir_practitioner(practitioner: PractitionerModel) -> dict:
    return content_resource("Practitioner", practitioner.practitioner_id, practitioner)
