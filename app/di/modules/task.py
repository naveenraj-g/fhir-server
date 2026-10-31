from dependency_injector import containers, providers

from app.repository.task import TaskRepository
from app.services.task import TaskService


class TaskContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    task_repository = providers.Factory(
        TaskRepository,
        session_factory=core.database.provided.session,
    )

    task_service = providers.Factory(
        TaskService,
        repository=task_repository,
    )
