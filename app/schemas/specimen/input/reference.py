from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class _SingleReferenceInput(BaseModel):
    """Shared shape for Specimen reference fields."""

    model_config = ConfigDict(extra="forbid")
    reference: str | None = Field(
        None, description="FHIR reference string, e.g. 'Patient/10001'."
    )
    reference_display: str | None = Field(
        None, description="Plain text narrative identifying the target."
    )
    reference_identifier_use: IdentifierUse | None = Field(
        None, description="Fallback identifier — its purpose, if known."
    )
    reference_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    reference_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    reference_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )


class SpecimenSubjectInput(_SingleReferenceInput):
    """Specimen.subject (0..1 Reference(Patient | Group | Device | Substance | Location))."""


class SpecimenParentInput(_SingleReferenceInput):
    """Specimen.parent (0..* Reference(Specimen))."""


class SpecimenRequestInput(_SingleReferenceInput):
    """Specimen.request (0..* Reference(ServiceRequest))."""


class SpecimenCollectorInput(_SingleReferenceInput):
    """Specimen.collection.collector (0..1 Reference(Practitioner | PractitionerRole))."""


class SpecimenAdditiveReferenceInput(_SingleReferenceInput):
    """Specimen.processing.additive and Specimen.container.additiveReference Reference(Substance)."""
