from dependency_injector import containers, providers

from app.repository.goal import GoalRepository
from app.services.goal import GoalService


class GoalContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    goal_repository = providers.Factory(
        GoalRepository,
        session_factory=core.database.provided.session,
    )

    goal_service = providers.Factory(
        GoalService,
        repository=goal_repository,
    )
