from fastapi import Depends, Path

from app.di.dependencies.service_request import get_service_request_service
from app.models.service_request import ServiceRequestModel
from app.services.service_request import ServiceRequestService


async def resolve_service_request(
    service_request_id: int = Path(..., ge=1, description="Public service_request identifier."),
    service: ServiceRequestService = Depends(get_service_request_service),
) -> ServiceRequestModel:
    """Loads a ServiceRequest by its public ID, 404 if missing — no
    ownership check (default/gateway-trusted pattern)."""
    return await service.get_by_service_request_id(service_request_id)
