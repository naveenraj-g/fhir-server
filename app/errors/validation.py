from app.errors.base import ApplicationError


class InputValidationError(ApplicationError):
    def __init__(self, errors: list[dict]):
        super().__init__(
            name="InputValidationError",
            message="Input validation failed",
            status_code=400,
            code="INPUT_VALIDATION_ERROR",
            metadata={"errors": errors},
        )
        self.errors = errors


class FhirValidationError(ApplicationError):
    """Raised when a payload, once converted to true FHIR JSON, fails the
    base R4 structural validator (app.fhir.validation.validate_base_r4) —
    or, later, the country/resource profile layers on top of it. 422, not
    400: the request body itself parsed and passed Pydantic's own schema
    (that's InputValidationError/RequestValidationError's job) — this is a
    semantic/structural FHIR violation one layer up, same status code as
    every other BusinessRuleViolationError in this codebase."""

    def __init__(self, errors: list[dict]):
        super().__init__(
            name="FhirValidationError",
            message="FHIR R4 validation failed",
            status_code=422,
            code="FHIR_VALIDATION_ERROR",
            metadata={"errors": errors},
        )
        self.errors = errors
