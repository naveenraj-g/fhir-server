"""PatientModel row -> FHIR R4 Patient. The only read-side mapper.

The resource is stored whole in PatientModel.content (see the model's
docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.patient import PatientModel


def to_fhir_patient(patient: PatientModel) -> dict:
    return content_resource("Patient", patient.patient_id, patient)
