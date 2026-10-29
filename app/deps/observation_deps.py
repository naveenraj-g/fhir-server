from fastapi import Depends, Path

from app.di.dependencies.observation import get_observation_service
from app.models.observation import ObservationModel
from app.services.observation import ObservationService


async def resolve_observation(
    observation_id: int = Path(..., ge=1, description="Public observation identifier."),
    service: ObservationService = Depends(get_observation_service),
) -> ObservationModel:
    """Loads an Observation by its public ID, 404 if missing — no
    ownership check (default/gateway-trusted pattern)."""
    return await service.get_by_observation_id(observation_id)
