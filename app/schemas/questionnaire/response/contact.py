from pydantic import BaseModel, Field

from app.schemas.datatypes import AuditFields, FHIRContactPoint, PlainContactPointRow


class FHIRQuestionnaireContact(BaseModel):
    """FHIR R4 ContactDetail — https://www.hl7.org/fhir/R4/metadatatypes.html#ContactDetail"""

    name: str | None = None
    telecom: list[FHIRContactPoint] | None = None


class PlainQuestionnaireContact(AuditFields):
    id: int = Field(..., description="Internal row ID.")
    name: str | None = Field(None, description="Name of an individual to contact.")
    telecoms: list[PlainContactPointRow] | None = Field(
        None, description="Contact details for individual or organization."
    )
