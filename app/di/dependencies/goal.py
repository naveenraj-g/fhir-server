from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.goal import GoalService


@inject
def get_goal_service(
    service: GoalService = Depends(
        Provide[Container.goal.goal_service]
    ),
) -> GoalService:
    return service
