from fastapi import Depends, Path

from app.di.dependencies.medication_request import get_medication_request_service
from app.models.medication_request import MedicationRequestModel
from app.services.medication_request import MedicationRequestService


async def resolve_medication_request(
    medication_request_id: int = Path(..., ge=1, description="Public medication_request identifier."),
    service: MedicationRequestService = Depends(get_medication_request_service),
) -> MedicationRequestModel:
    """Loads a MedicationRequest by its public ID, 404 if missing — no
    ownership check (default/gateway-trusted pattern)."""
    return await service.get_by_medication_request_id(medication_request_id)
