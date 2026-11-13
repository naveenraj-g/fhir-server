from pydantic import Field

from app.schemas.fhir_input.base import FhirInputModel


class FhirCodingInput(FhirInputModel):
    """FHIR R4 Coding — a reference to a code defined by a terminology system."""

    system: str | None = Field(
        None,
        description="The identification of the code system that defines the meaning of the symbol in the code.",
    )
    version: str | None = Field(
        None,
        description="The version of the code system which was used when choosing this code.",
    )
    code: str | None = Field(None, description="A symbol in syntax defined by the code system.")
    display: str | None = Field(
        None,
        description="A representation of the meaning of the code in the system, following the rules of the system.",
    )
    userSelected: bool | None = Field(
        None,
        description="Indicates that this coding was chosen by a user directly, e.g. off a pick list of available items.",
    )
