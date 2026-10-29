from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.encounter import EncounterService


@inject
def get_encounter_service(
    service: EncounterService = Depends(Provide[Container.encounter.encounter_service]),
) -> EncounterService:
    return service
