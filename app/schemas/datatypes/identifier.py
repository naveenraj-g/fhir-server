from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.datatypes.codeable_concept import FHIRCodeableConcept
from app.schemas.datatypes.period import FHIRPeriod
from app.schemas.datatypes.reference import FHIRReference


class FHIRIdentifier(BaseModel):
    """FHIR R4 Identifier — a business identifier for a resource, unique within
    some defined namespace."""

    use: Optional[str] = Field(
        None, description="The purpose of this identifier. usual|official|temp|secondary|old."
    )
    type: Optional[FHIRCodeableConcept] = Field(
        None, description="A coded description of the type of identifier (e.g. MR, SSN, passport)."
    )
    system: Optional[str] = Field(
        None, description="The namespace (a URI) that identifies the scope this identifier's value is unique within."
    )
    value: Optional[str] = Field(None, description="The identifier value itself, unique within the given system.")
    period: Optional[FHIRPeriod] = Field(
        None, description="The period during which this identifier is/was valid for use."
    )
    assigner: Optional[FHIRReference] = Field(
        None, description="Reference(Organization) — the organization that issued this identifier."
    )


# Resolves FHIRReference.identifier's "FHIRIdentifier" forward ref now that
# FHIRIdentifier exists — see app.schemas.datatypes.reference's docstring.
FHIRReference.model_rebuild(_types_namespace={"FHIRIdentifier": FHIRIdentifier})
