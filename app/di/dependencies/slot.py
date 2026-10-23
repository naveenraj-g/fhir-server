from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.slot import SlotService


@inject
def get_slot_service(
    service: SlotService = Depends(Provide[Container.slot.slot_service]),
) -> SlotService:
    return service
