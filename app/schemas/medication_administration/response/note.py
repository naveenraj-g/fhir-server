from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.datatypes import AuditFields, FHIRReference
from app.schemas.enums import IdentifierUse


class FHIRAnnotation(BaseModel):
    """FHIR R4 Annotation."""

    model_config = ConfigDict(extra="allow")

    authorReference: FHIRReference | None = None
    authorString: str | None = None
    time: str | None = None
    text: str


class PlainMedicationAdministrationNoteAuthor(BaseModel):
    model_config = ConfigDict(extra="allow")

    reference: str | None = None
    type: str | None = None
    id: int | None = None
    display: str | None = None
    identifier_use: IdentifierUse | None = None
    identifier_type_system: str | None = None
    identifier_type_version: str | None = None
    identifier_type_code: str | None = None
    identifier_type_display: str | None = None
    identifier_type_user_selected: bool | None = None
    identifier_type_text: str | None = None
    identifier_system: str | None = None
    identifier_value: str | None = None
    identifier_period_start: datetime | None = None
    identifier_period_end: datetime | None = None


class PlainMedicationAdministrationNote(BaseModel):
    model_config = ConfigDict(extra="allow")

    text: str
    time: datetime | None = None
    author_string: str | None = None
    author_reference: PlainMedicationAdministrationNoteAuthor | None = None


class MedicationAdministrationNoteListItem(AuditFields):
    model_config = ConfigDict(extra="allow")

    id: int
    text: str
    time: datetime | None = None
    author_string: str | None = None
    author_reference: str | None = None
    author_type: str | None = None
    author_id: int | None = None
    author_display: str | None = None


class MedicationAdministrationNoteListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    data: list[MedicationAdministrationNoteListItem]
