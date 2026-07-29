from fastapi import Depends, Path

from app.di.dependencies.patient import get_patient_service
from app.models.patient.patient import PatientModel
from app.services.patient_service import PatientService


async def resolve_patient(
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    patient_service: PatientService = Depends(get_patient_service),
) -> PatientModel:
    """Load patient by public id — get_patient() raises NotFoundError (404) if missing."""
    return await patient_service.get_patient(patient_id)
