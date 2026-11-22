"""MedicationModel row -> FHIR R4 Medication. The only
read-side mapper.

The resource is stored whole in MedicationModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.medication import MedicationModel


def to_fhir_medication(medication: MedicationModel) -> dict:
    return content_resource("Medication", medication.medication_id, medication)
