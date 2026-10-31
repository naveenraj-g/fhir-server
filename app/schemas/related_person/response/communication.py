from pydantic import BaseModel, Field

from app.schemas.datatypes import AuditFields, FHIRCodeableConcept, PlainCodingRow


class FHIRRelatedPersonCommunication(BaseModel):
    language: FHIRCodeableConcept = Field(
        ...,
        description="The language which can be used to communicate with the patient about his or her health.",
    )
    preferred: bool | None = Field(
        None, description="Language preference indicator."
    )


class PlainRelatedPersonCommunication(AuditFields):
    id: int = Field(..., description="Internal row ID.")
    language_text: str | None = Field(
        None, description="The human language representation of the language."
    )
    language_codings: list[PlainCodingRow] | None = Field(
        None, description="Coding(s) for the language."
    )
    preferred: bool | None = Field(
        None, description="Language preference indicator."
    )
