from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRContactPoint, PlainContactPointRow


class FHIRPlanDefinitionContact(BaseModel):
    """FHIR R4 ContactDetail."""

    model_config = ConfigDict(extra="allow")

    name: str | None = None
    telecom: list[FHIRContactPoint] | None = None


class PlainPlanDefinitionContact(BaseModel):
    """Plain ContactDetail representation."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    name: str | None = Field(None, description="Name of an individual to contact.")
    telecoms: list[PlainContactPointRow] | None = Field(
        None, description="Contact details for individual or organization."
    )
