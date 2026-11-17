from app.errors.base import ApplicationError
from app.errors.fhir_codes import IssueType


class InfrastructureError(ApplicationError):
    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(
            name="InfrastructureError",
            message=message,
            status_code=500,
            code="INFRASTRUCTURE_ERROR",
            issue_type=IssueType.EXCEPTION,
            cause=cause,
            is_operational=False,
        )


class DatabaseError(ApplicationError):
    def __init__(self, message="Database operation failed", cause=None):
        super().__init__(
            name="DatabaseError",
            message=message,
            status_code=500,
            code="DATABASE_ERROR",
            # "The persistent store is unavailable" is a more specific,
            # correct description of this class's actual meaning than the
            # generic "exception" default.
            issue_type=IssueType.NO_STORE,
            cause=cause,
            is_operational=False,
        )


class ValidatorUnavailableError(ApplicationError):
    """The external FHIR validator could not be used (unreachable, timed out,
    or a server error) and `fhir_validation.java_validator.fallback_to_native`
    is off, so there is nothing to fall back to. 503, not 500 — the request
    itself is fine and can be retried once the validator is back."""

    def __init__(self, message="FHIR validator is unavailable", cause=None):
        super().__init__(
            name="ValidatorUnavailableError",
            message=message,
            status_code=503,
            code="VALIDATOR_UNAVAILABLE",
            issue_type=IssueType.TRANSIENT,
            cause=cause,
            is_operational=True,
        )
