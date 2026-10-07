from app.errors.base import ApplicationError
from app.errors.fhir_codes import IssueType


class BusinessRuleViolationError(ApplicationError):
    def __init__(self, message: str, metadata=None):
        super().__init__(
            name="BusinessRuleViolationError",
            message=message,
            status_code=422,
            code="BUSINESS_RULE_VIOLATION",
            issue_type=IssueType.BUSINESS_RULE,
            metadata=metadata,
        )


class ResourceConflictError(ApplicationError):
    def __init__(self, message: str):
        super().__init__(
            name="ResourceConflictError",
            message=message,
            status_code=409,
            code="RESOURCE_CONFLICT",
            issue_type=IssueType.CONFLICT,
        )


class NotFoundError(ApplicationError):
    """Raised by service methods when a requested resource doesn't exist (or,
    for tenant-scoped lookups, doesn't match the caller's org/user) — lets the
    service raise directly instead of returning None for the router to check."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            name="NotFoundError",
            message=message,
            status_code=404,
            code="NOT_FOUND",
            issue_type=IssueType.NOT_FOUND,
        )
