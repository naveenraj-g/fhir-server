from pydantic import BaseModel, ConfigDict, Field


class ActivityDefinitionDynamicValueInput(BaseModel):
    """ActivityDefinition.dynamicValue input schema."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., description="The path to the element to be set dynamically.")
    expression_description: str | None = Field(None, description="Natural language description of the condition.")
    expression_name: str | None = Field(None, description="Short name assigned to expression for reuse.")
    expression_language: str | None = Field(None, description="text/cql | text/fhirpath | application/x-fhir-query | etc.")
    expression_expression: str | None = Field(None, description="An expression in the specified language.")
    expression_reference: str | None = Field(None, description="Where the expression is found.")
