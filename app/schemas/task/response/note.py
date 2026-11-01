from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import AuditFields
from app.schemas.datatypes.reference import FHIRReference


class FHIRTaskAnnotation(BaseModel):
    """FHIR R4 Annotation element."""

    authorString: str | None = None
    authorReference: FHIRReference | None = None
    time: str | None = None
    text: str


class PlainTaskNote(AuditFields):
    """Plain snake_case serialization of a Task note child row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="DB primary key of this note row.")
    author_string: str | None = None
    author_reference: str | None = None
    author_type: str | None = None
    author_id: int | None = None
    author_display: str | None = None
    author_identifier_use: str | None = None
    author_identifier_type_system: str | None = None
    author_identifier_type_version: str | None = None
    author_identifier_type_code: str | None = None
    author_identifier_type_display: str | None = None
    author_identifier_type_user_selected: bool | None = None
    author_identifier_type_text: str | None = None
    author_identifier_system: str | None = None
    author_identifier_value: str | None = None
    author_identifier_period_start: str | None = None
    author_identifier_period_end: str | None = None
    time: str | None = None
    text: str = Field(..., description="Annotation content.")
