from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.family_member_history import FamilyMemberHistoryService


@inject
def get_family_member_history_service(
    service: FamilyMemberHistoryService = Depends(
        Provide[Container.family_member_history.family_member_history_service]
    ),
) -> FamilyMemberHistoryService:
    return service
