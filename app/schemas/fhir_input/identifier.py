from pydantic import Field

from app.schemas.enums import IdentifierUse
from app.schemas.fhir_input.base import FhirInputModel
from app.schemas.fhir_input.codeable_concept import FhirCodeableConceptInput
from app.schemas.fhir_input.period import FhirPeriodInput
from app.schemas.fhir_input.reference import FhirReferenceInput


class FhirIdentifierInput(FhirInputModel):
    """FHIR R4 Identifier — a business identifier for the resource."""

    use: IdentifierUse | None = Field(
        None, description="usual | official | temp | secondary | old (if known)."
    )
    type: FhirCodeableConceptInput | None = Field(
        None, description="Description of identifier (e.g. NPI, tax ID, license)."
    )
    system: str | None = Field(
        None,
        description="Establishes the namespace for the value — a URL that describes a set of unique values.",
    )
    value: str | None = Field(
        None, description="The value that is unique within the system."
    )
    period: FhirPeriodInput | None = Field(
        None, description="Time period when the identifier is/was valid for use."
    )
    assigner: FhirReferenceInput | None = Field(
        None, description="Organization that issued the identifier — Reference(Organization)."
    )


# Reference.identifier is itself an Identifier (whose assigner is a
# Reference) — resolve the forward reference now that both exist.
FhirReferenceInput.model_rebuild(_types_namespace={"FhirIdentifierInput": FhirIdentifierInput})
