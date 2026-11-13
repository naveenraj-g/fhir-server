from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from app.schemas.fhir_input.base import FhirInputModel

if TYPE_CHECKING:
    from app.schemas.fhir_input.identifier import FhirIdentifierInput


class FhirReferenceInput(FhirInputModel):
    """FHIR R4 Reference. When `reference` is a relative `Type/id` to a
    resource this system holds, it must exist in the caller's org (checked
    at write time)."""

    reference: str | None = Field(
        None,
        description="Literal reference — a relative 'ResourceType/id' (e.g. 'Organization/190001') or an absolute URL.",
    )
    type: str | None = Field(
        None,
        description="Type the reference refers to (e.g. 'Organization') — a FHIR resource type URI.",
    )
    identifier: FhirIdentifierInput | None = Field(
        None,
        description="Logical reference, when a literal reference is not known (the target isn't a resource in this system).",
    )
    display: str | None = Field(
        None, description="Text alternative for the resource."
    )
