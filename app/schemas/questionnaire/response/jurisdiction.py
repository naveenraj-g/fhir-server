from pydantic import Field

from app.schemas.datatypes import AuditFields, PlainCodingRow


class PlainQuestionnaireJurisdiction(AuditFields):
    id: int = Field(..., description="Internal row ID.")
    codings: list[PlainCodingRow] | None = Field(None, description="Coding(s) for this jurisdiction.")
    text: str | None = Field(None, description="A human language representation of the jurisdiction.")
