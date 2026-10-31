from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.care_team import CareTeamService


@inject
def get_care_team_service(
    service: CareTeamService = Depends(
        Provide[Container.care_team.care_team_service]
    ),
) -> CareTeamService:
    return service
