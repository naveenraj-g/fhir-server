from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.core.request_context import request_id_ctx_var
from app.errors.base import ApplicationError
from app.errors.fhir_codes import IssueType
from app.errors.validation import FhirValidationError, InputValidationError

logger = get_logger(__name__)

# Pydantic v2's own ValidationError `type` string -> the nearest real HL7
# IssueType. Not exhaustive (Pydantic has many more specific type strings
# than FHIR has matching issue types) — anything unmapped falls back to
# IssueType.INVALID (the parent code), which is always a legal choice, just
# less specific. Mirrors app/fhir/validation/base_r4.py's
# _JSONSCHEMA_KEYWORD_TO_ISSUE_TYPE for the same reason: same kind of gap,
# same pragmatic answer.
_PYDANTIC_TYPE_TO_ISSUE_TYPE = {
    "missing": IssueType.REQUIRED,
    "extra_forbidden": IssueType.STRUCTURE,
}


def _pydantic_issue_type(err: dict) -> IssueType:
    return _PYDANTIC_TYPE_TO_ISSUE_TYPE.get(err.get("type"), IssueType.INVALID)


def _base_log_payload(request: Request):
    return {
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
    }


def get_request_id(request: Request) -> str | None:
    """Prefers the ContextVar over request.state — an error handler must never
    itself raise, and request.state.request_id is unset whenever the
    request-context middleware didn't run (e.g. an exception raised in a
    middleware layered above it)."""
    return request_id_ctx_var.get() or getattr(request.state, "request_id", None)


def _issue(
    severity: str,
    issue_type: IssueType,
    diagnostics: str | None = None,
    expression: list[str] | None = None,
    details: dict | None = None,
) -> dict:
    """Builds one OperationOutcome.issue entry — the one place that shape
    gets assembled, so every handler branch emits the same field set."""
    issue: dict = {"severity": severity, "code": issue_type.value}
    if details:
        issue["details"] = details
    if diagnostics:
        issue["diagnostics"] = diagnostics
    if expression:
        issue["expression"] = expression
    return issue


# -------------------------------------------------------
# ApplicationError (Your Domain Errors)
# -------------------------------------------------------
async def application_error_handler(request: Request, exc: ApplicationError):
    payload = _base_log_payload(request)
    is_server_error = exc.status_code >= 500
    request_id = get_request_id(request)

    payload.update(
        {
            "error_name": exc.name,
            "error_code": exc.code,
            "issue_type": exc.issue_type.value,
            "status_code": exc.status_code,
            "metadata": exc.metadata,
        }
    )

    # -----------------------
    # Input Validation Error
    # -----------------------
    if isinstance(exc, InputValidationError):
        logger.info(
            "Input validation failed",
            extra={**payload, "event": "error.input_validation"},
        )

        return JSONResponse(
            status_code=400,
            content={
                "resourceType": "OperationOutcome",
                "issue": [
                    _issue(
                        "error",
                        error.get("issue_type", InputValidationError.DEFAULT_ISSUE_TYPE),
                        diagnostics=error["message"],
                        expression=[error["field"]],
                        details=error.get("details"),
                    )
                    for error in exc.errors
                ],
            },
            headers=({"X-Request-ID": request_id} if request_id else None),
        )

    # -----------------------
    # FHIR Base R4 Validation Error
    # -----------------------
    if isinstance(exc, FhirValidationError):
        logger.info(
            "FHIR base R4 validation failed",
            extra={**payload, "event": "error.fhir_validation"},
        )

        return JSONResponse(
            status_code=422,
            content={
                "resourceType": "OperationOutcome",
                "issue": [
                    _issue(
                        "error",
                        error.get("issue_type", FhirValidationError.DEFAULT_ISSUE_TYPE),
                        diagnostics=error["message"],
                        expression=[error["field"]],
                        details=error.get("details"),
                    )
                    for error in exc.errors
                ],
            },
            headers=({"X-Request-ID": request_id} if request_id else None),
        )

    # -----------------------
    # Operational Errors
    # -----------------------
    if exc.is_operational:
        logger.warning(
            "Operational application error",
            extra={**payload, "event": "error.operational"},
        )
    else:
        logger.error(
            "Non-operational application error",
            extra={**payload, "event": "error.non_operational"},
            exc_info=True,
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "resourceType": "OperationOutcome",
            "issue": [
                _issue(
                    exc.severity.value,
                    exc.issue_type,
                    diagnostics=(
                        "Internal server error" if is_server_error else exc.message
                    ),
                    details=exc.details,
                )
            ],
        },
        headers=({"X-Request-ID": request_id} if request_id else None),
    )


# -------------------------------------------------------
# Request Validation (Pydantic Input Schema Errors)
# -------------------------------------------------------
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    payload = _base_log_payload(request)
    request_id = get_request_id(request)

    logger.info(
        "Request schema validation failed",
        extra={
            **payload,
            "event": "error.schema_validation",
            "errors": exc.errors(),
        },
    )

    issues = []

    for err in exc.errors():
        field_path = ".".join(str(loc) for loc in err["loc"] if loc != "body")

        issues.append(
            _issue(
                "error",
                _pydantic_issue_type(err),
                diagnostics=err["msg"],
                expression=[field_path],
            )
        )

    return JSONResponse(
        status_code=422,
        content={
            "resourceType": "OperationOutcome",
            "issue": issues,
        },
        headers=({"X-Request-ID": request_id} if request_id else None),
    )


# -------------------------------------------------------
# Response Validation (Server Bug)
# -------------------------------------------------------
async def response_validation_exception_handler(
    request: Request, exc: ResponseValidationError
):
    payload = _base_log_payload(request)
    request_id = get_request_id(request)

    logger.critical(
        "Response validation failed",
        extra={**payload, "event": "error.response_validation"},
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "resourceType": "OperationOutcome",
            "issue": [_issue("error", IssueType.EXCEPTION, diagnostics="Internal server error")],
        },
        headers=({"X-Request-ID": request_id} if request_id else None),
    )


# -------------------------------------------------------
# Unhandled Exceptions (Crash)
# -------------------------------------------------------
async def unhandled_exception_handler(request: Request, exc: Exception):
    payload = _base_log_payload(request)
    request_id = get_request_id(request)

    payload.update(
        {
            "error_type": type(exc).__name__,
        }
    )

    logger.critical(
        "Unhandled exception occurred",
        extra={**payload, "event": "error.unhandled"},
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "resourceType": "OperationOutcome",
            "issue": [_issue("error", IssueType.EXCEPTION, diagnostics="Internal server error")],
        },
        headers=({"X-Request-ID": request_id} if request_id else None),
    )


# Maps an HTTPException's bare status code to a real IssueType — used only
# here, for FastAPI's own HTTPException, which (unlike ApplicationError) has
# no issue_type of its own to carry. Deliberately small and status-driven,
# since an HTTPException raised ad hoc genuinely has nothing more specific
# attached to it.
_HTTP_STATUS_TO_ISSUE_TYPE = {
    400: IssueType.INVALID,
    401: IssueType.SECURITY,
    403: IssueType.FORBIDDEN,
    404: IssueType.NOT_FOUND,
    409: IssueType.CONFLICT,
    422: IssueType.PROCESSING,
    500: IssueType.EXCEPTION,
}


async def http_exception_handler(request: Request, exc: HTTPException):
    payload = _base_log_payload(request)
    request_id = get_request_id(request)

    logger.warning(
        "HTTP exception raised",
        extra={
            **payload,
            "event": "error.http_exception",
            "status_code": exc.status_code,
            "detail": exc.detail,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "resourceType": "OperationOutcome",
            "issue": [
                _issue(
                    "error",
                    _HTTP_STATUS_TO_ISSUE_TYPE.get(exc.status_code, IssueType.PROCESSING),
                    diagnostics=exc.detail,
                )
            ],
        },
        headers=({"X-Request-ID": request_id} if request_id else None),
    )
