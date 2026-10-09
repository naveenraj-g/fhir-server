from pydantic import BaseModel


class OperationOutcomeIssueSchema(BaseModel):
    severity: str
    code: str
    diagnostics: str | None = None
    expression: list[str] | None = None
    details: dict | None = None


class OperationOutcomeSchema(BaseModel):
    resourceType: str = "OperationOutcome"
    issue: list[OperationOutcomeIssueSchema]
