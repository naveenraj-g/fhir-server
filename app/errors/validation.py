from app.errors.base import ApplicationError
from app.errors.fhir_codes import IssueType


class InputValidationError(ApplicationError):
    """Raised for a Pydantic schema-validation failure. `errors` is a list
    of `{"field": str, "message": str}` dicts, each optionally carrying its
    own `"issue_type": IssueType` — falls back to `default_issue_type`
    (DEFAULT_ISSUE_TYPE below) for any entry that doesn't specify one, since
    most Pydantic errors don't yet carry enough information to pick a more
    specific code than the generic "invalid"."""

    DEFAULT_ISSUE_TYPE = IssueType.INVALID

    def __init__(self, errors: list[dict]):
        super().__init__(
            name="InputValidationError",
            message="Input validation failed",
            status_code=400,
            code="INPUT_VALIDATION_ERROR",
            issue_type=self.DEFAULT_ISSUE_TYPE,
            metadata={"errors": errors},
        )
        self.errors = errors


class FhirValidationError(ApplicationError):
    """Raised when a payload, once converted to true FHIR JSON, fails base
    R4 (or, once built, country/organization profile) validation. 422, not
    400: the request body itself parsed and passed Pydantic's own schema
    (that's InputValidationError/RequestValidationError's job) — this is a
    semantic/structural FHIR violation one layer up, same status code as
    every other BusinessRuleViolationError in this codebase.

    `errors` is a list of `{"field": str, "message": str}` dicts, each
    optionally carrying its own `"issue_type": IssueType` (and optionally
    `"details"`, a CodeableConcept dict for a more specific sub-code) —
    the java_validator backend already computes a precise IssueType per
    issue (e.g. "invariant" for a constraint failure) and preserves it
    through to here; falls back to DEFAULT_ISSUE_TYPE only for entries
    that don't specify one (e.g. from the native/jsonschema backend, which
    has a looser but still real mapping of its own — see base_r4.py)."""

    DEFAULT_ISSUE_TYPE = IssueType.INVALID

    def __init__(self, errors: list[dict]):
        super().__init__(
            name="FhirValidationError",
            message="FHIR R4 validation failed",
            status_code=422,
            code="FHIR_VALIDATION_ERROR",
            issue_type=self.DEFAULT_ISSUE_TYPE,
            metadata={"errors": errors},
        )
        self.errors = errors
