from typing import Optional
from pydantic import BaseModel, Field


class FHIRReference(BaseModel):
    """FHIR R4 Reference — a reference from one resource to another.

    `identifier` is typed as a forward-ref string to avoid a circular import
    with app.schemas.datatypes.identifier (FHIRIdentifier.assigner is itself
    a FHIRReference) — app.schemas.datatypes.identifier resolves it via
    `FHIRReference.model_rebuild(_types_namespace=...)` right after defining
    FHIRIdentifier."""

    reference: Optional[str] = Field(
        None, description="A literal reference to another resource, e.g. 'Organization/100'."
    )
    display: Optional[str] = Field(
        None, description="Plain-text display alternative for the referenced resource."
    )
    identifier: Optional["FHIRIdentifier"] = Field(
        None,
        description=(
            "Logical reference via a business identifier, used instead of (or "
            "alongside) `reference` when the target isn't a resource in this system."
        ),
    )
