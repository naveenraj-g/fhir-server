"""MedicationAdministrationModel row -> FHIR R4 MedicationAdministration. The only
read-side mapper.

The resource is stored whole in MedicationAdministrationModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.medication_administration import MedicationAdministrationModel


def to_fhir_medication_administration(
    medication_administration: MedicationAdministrationModel,
) -> dict:
    return content_resource(
        "MedicationAdministration",
        medication_administration.medication_administration_id,
        medication_administration,
    )
