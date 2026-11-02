from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.detected_issue import DetectedIssueService


@inject
def get_detected_issue_service(
    service: DetectedIssueService = Depends(
        Provide[Container.detected_issue.detected_issue_service]
    ),
) -> DetectedIssueService:
    return service
