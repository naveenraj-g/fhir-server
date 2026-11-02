from dependency_injector import containers, providers

from app.repository.detected_issue import DetectedIssueRepository
from app.services.detected_issue import DetectedIssueService


class DetectedIssueContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    detected_issue_repository = providers.Factory(
        DetectedIssueRepository,
        session_factory=core.database.provided.session,
    )

    detected_issue_service = providers.Factory(
        DetectedIssueService,
        repository=detected_issue_repository,
    )
