"""MedicationDispenseModel row -> FHIR R4 MedicationDispense. The only
read-side mapper.

The resource is stored whole in MedicationDispenseModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.medication_dispense import MedicationDispenseModel


def to_fhir_medication_dispense(medication_dispense: MedicationDispenseModel) -> dict:
    return content_resource(
        "MedicationDispense",
        medication_dispense.medication_dispense_id,
        medication_dispense,
    )
