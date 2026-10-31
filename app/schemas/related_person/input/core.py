from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import AdministrativeGender

from .address import RelatedPersonAddressInput
from .communication import RelatedPersonCommunicationInput
from .identifier import RelatedPersonIdentifierInput
from .name import RelatedPersonNameInput
from .photo import RelatedPersonPhotoInput
from .relationship import RelatedPersonRelationshipInput
from .telecom import RelatedPersonTelecomInput

_EXAMPLE = {
    "active": True,
    "patient": "Patient/10001",
    "patient_display": "John Doe",
    "relationship": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                    "code": "WIFE",
                    "display": "wife",
                }
            ],
            "text": "Wife",
        }
    ],
    "name": [
        {
            "use": "official",
            "family": "Doe",
            "given": ["Jane"],
        }
    ],
    "telecom": [
        {
            "system": "phone",
            "value": "555-0100",
            "use": "home",
        }
    ],
    "gender": "female",
    "birth_date": "1982-05-14",
    "address": [
        {
            "use": "home",
            "line": ["123 Main St"],
            "city": "Metropolis",
            "state": "NY",
            "postal_code": "10001",
            "country": "USA",
        }
    ],
    "period_start": "2020-01-01T00:00:00Z",
    "communication": [
        {
            "language_coding": [
                {
                    "system": "urn:ietf:bcp:47",
                    "code": "en",
                    "display": "English",
                }
            ],
            "language_text": "English",
            "preferred": True,
        }
    ],
}


class RelatedPersonCreateSchema(BaseModel):
    """Request body for POST /api/fhir/v1/related_persons.

    RelatedPerson is an org-scoped entity and has no user_id.
    patient is required (1..1 Reference(Patient)).
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _EXAMPLE},
    )

    identifier: list[RelatedPersonIdentifierInput] | None = Field(
        None, description="An identifier for this person."
    )
    active: bool | None = Field(
        None, description="Whether this related person's record is in active use."
    )
    patient: str = Field(
        ...,
        description="The patient this person is related to, as a FHIR reference string (e.g. 'Patient/10001').",
    )
    patient_display: str | None = Field(
        None, description="Plain text display for the patient reference."
    )
    relationship: list[RelatedPersonRelationshipInput] | None = Field(
        None,
        description="The nature of the relationship between a patient and the related person.",
    )
    name: list[RelatedPersonNameInput] | None = Field(
        None, description="A name associated with the person."
    )
    telecom: list[RelatedPersonTelecomInput] | None = Field(
        None, description="A contact detail for the person."
    )
    gender: AdministrativeGender | None = Field(
        None, description="male | female | other | unknown."
    )
    birth_date: date | None = Field(
        None, description="The date on which the related person was born."
    )
    address: list[RelatedPersonAddressInput] | None = Field(
        None, description="Address where the related person can be contacted or visited."
    )
    photo: list[RelatedPersonPhotoInput] | None = Field(
        None, description="Image of the person."
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the period of time that this relationship is considered valid.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period of time that this relationship is considered valid.",
    )
    communication: list[RelatedPersonCommunicationInput] | None = Field(
        None,
        description="A language which may be used to communicate with about the patient's health.",
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions."
    )


class RelatedPersonPatchSchema(BaseModel):
    """Request body for PATCH /api/fhir/v1/related_persons/{id}.

    All fields optional; omitted fields are unchanged; supplied sub-resource lists replace wholesale.
    """

    model_config = ConfigDict(extra="forbid")

    identifier: list[RelatedPersonIdentifierInput] | None = Field(
        None, description="An identifier for this person."
    )
    active: bool | None = Field(
        None, description="Whether this related person's record is in active use."
    )
    patient: str | None = Field(
        None,
        description="The patient this person is related to, as a FHIR reference string (e.g. 'Patient/10001').",
    )
    patient_display: str | None = Field(
        None, description="Plain text display for the patient reference."
    )
    relationship: list[RelatedPersonRelationshipInput] | None = Field(
        None,
        description="The nature of the relationship between a patient and the related person.",
    )
    name: list[RelatedPersonNameInput] | None = Field(
        None, description="A name associated with the person."
    )
    telecom: list[RelatedPersonTelecomInput] | None = Field(
        None, description="A contact detail for the person."
    )
    gender: AdministrativeGender | None = Field(
        None, description="male | female | other | unknown."
    )
    birth_date: date | None = Field(
        None, description="The date on which the related person was born."
    )
    address: list[RelatedPersonAddressInput] | None = Field(
        None, description="Address where the related person can be contacted or visited."
    )
    photo: list[RelatedPersonPhotoInput] | None = Field(
        None, description="Image of the person."
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the period of time that this relationship is considered valid.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period of time that this relationship is considered valid.",
    )
    communication: list[RelatedPersonCommunicationInput] | None = Field(
        None,
        description="A language which may be used to communicate with about the patient's health.",
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions."
    )
