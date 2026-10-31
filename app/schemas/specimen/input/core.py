from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import SpecimenStatus

from .codeable_concept import SpecimenCodeableConceptInput
from .collection import SpecimenCollectionInput
from .container import SpecimenContainerInput
from .identifier import SpecimenIdentifierInput
from .note import SpecimenNoteInput
from .processing import SpecimenProcessingInput
from .reference import (
    SpecimenParentInput,
    SpecimenRequestInput,
    SpecimenSubjectInput,
)

_EXAMPLE = {
    "status": "available",
    "type": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "122555007",
                "display": "Venous blood specimen",
            }
        ],
        "text": "Venous blood specimen",
    },
    "subject": {
        "reference": "Patient/10001",
        "reference_display": "Jane Doe",
    },
    "received_time": "2023-01-15T10:30:00Z",
    "collection": {
        "collector": {
            "reference": "Practitioner/30001",
            "reference_display": "Dr. Alice Smith",
        },
        "collected_date_time": "2023-01-15T09:30:00Z",
        "quantity_value": 10.0,
        "quantity_unit": "mL",
        "quantity_system": "http://unitsofmeasure.org",
        "quantity_code": "mL",
    },
}


class SpecimenCreateSchema(BaseModel):
    """Request body for POST /api/fhir/v1/specimens."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _EXAMPLE},
    )

    identifier: list[SpecimenIdentifierInput] | None = Field(
        None, description="External identifiers for this specimen."
    )
    accession_identifier: SpecimenIdentifierInput | None = Field(
        None, description="Identifier assigned by the lab when the specimen was received."
    )
    status: SpecimenStatus | None = Field(
        None, description="available | unavailable | unsatisfactory | entered-in-error."
    )
    type: SpecimenCodeableConceptInput | None = Field(
        None, description="Kind for specimen."
    )
    subject: SpecimenSubjectInput | None = Field(
        None, description="Where the specimen came from (Patient | Group | Device | Substance | Location)."
    )
    received_time: datetime | None = Field(
        None, description="The time when specimen was received for processing."
    )
    parent: list[SpecimenParentInput] | None = Field(
        None, description="Specimen from which this specimen originated."
    )
    request: list[SpecimenRequestInput] | None = Field(
        None, description="Why the specimen was collected (ServiceRequest)."
    )
    collection: SpecimenCollectionInput | None = Field(
        None, description="Collection details."
    )
    processing: list[SpecimenProcessingInput] | None = Field(
        None, description="Processing and manipulation details."
    )
    container: list[SpecimenContainerInput] | None = Field(
        None, description="Direct container of specimen."
    )
    condition: list[SpecimenCodeableConceptInput] | None = Field(
        None, description="State of the specimen (e.g. frozen, cooled)."
    )
    note: list[SpecimenNoteInput] | None = Field(
        None, description="Comments."
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions."
    )


class SpecimenPatchSchema(BaseModel):
    """Request body for PATCH /api/fhir/v1/specimens/{id}."""

    model_config = ConfigDict(extra="forbid")

    identifier: list[SpecimenIdentifierInput] | None = Field(
        None, description="External identifiers for this specimen."
    )
    accession_identifier: SpecimenIdentifierInput | None = Field(
        None, description="Identifier assigned by the lab when the specimen was received."
    )
    status: SpecimenStatus | None = Field(
        None, description="available | unavailable | unsatisfactory | entered-in-error."
    )
    type: SpecimenCodeableConceptInput | None = Field(
        None, description="Kind for specimen."
    )
    subject: SpecimenSubjectInput | None = Field(
        None, description="Where the specimen came from (Patient | Group | Device | Substance | Location)."
    )
    received_time: datetime | None = Field(
        None, description="The time when specimen was received for processing."
    )
    parent: list[SpecimenParentInput] | None = Field(
        None, description="Specimen from which this specimen originated."
    )
    request: list[SpecimenRequestInput] | None = Field(
        None, description="Why the specimen was collected (ServiceRequest)."
    )
    collection: SpecimenCollectionInput | None = Field(
        None, description="Collection details."
    )
    processing: list[SpecimenProcessingInput] | None = Field(
        None, description="Processing and manipulation details."
    )
    container: list[SpecimenContainerInput] | None = Field(
        None, description="Direct container of specimen."
    )
    condition: list[SpecimenCodeableConceptInput] | None = Field(
        None, description="State of the specimen (e.g. frozen, cooled)."
    )
    note: list[SpecimenNoteInput] | None = Field(
        None, description="Comments."
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions."
    )
