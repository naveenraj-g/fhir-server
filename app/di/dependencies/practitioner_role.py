from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.practitioner_role import PractitionerRoleService


@inject
def get_practitioner_role_service(
    service: PractitionerRoleService = Depends(
        Provide[Container.practitioner_role.practitioner_role_service]
    ),
) -> PractitionerRoleService:
    return service
