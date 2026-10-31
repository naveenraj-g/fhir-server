from pydantic import BaseModel, ConfigDict, Field


class FHIRActivityDefinitionExpression(BaseModel):
    """FHIR R4 Expression."""

    model_config = ConfigDict(extra="allow")

    description: str | None = None
    name: str | None = None
    language: str | None = None
    expression: str | None = None
    reference: str | None = None


class FHIRActivityDefinitionDynamicValue(BaseModel):
    """FHIR R4 ActivityDefinition.dynamicValue."""

    model_config = ConfigDict(extra="allow")

    path: str
    expression: FHIRActivityDefinitionExpression | None = None


class PlainActivityDefinitionDynamicValue(BaseModel):
    """Plain dynamicValue representation."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    path: str
    expression_description: str | None = None
    expression_name: str | None = None
    expression_language: str | None = None
    expression_expression: str | None = None
    expression_reference: str | None = None
