from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.repository._reference_shared import _IDENTIFIER_FALLBACK_SUFFIXES
from app.schemas.enums import AdministrativeGender, IdentifierUse

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
    patient is required (1..1 Reference(Patient)) — either patient literal URL,
    patient_identifier_* fallback, or patient_display must be provided.
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
    patient: str | None = Field(
        None,
        description="The patient this person is related to, as a FHIR reference string (e.g. 'Patient/10001').",
    )
    patient_display: str | None = Field(
        None, description="Plain text display for the patient reference."
    )
    patient_identifier_use: IdentifierUse | None = Field(
        None, description="Patient identifier use."
    )
    patient_identifier_type_system: str | None = Field(
        None, description="Patient identifier type system."
    )
    patient_identifier_type_version: str | None = Field(
        None, description="Patient identifier type version."
    )
    patient_identifier_type_code: str | None = Field(
        None, description="Patient identifier type code."
    )
    patient_identifier_type_display: str | None = Field(
        None, description="Patient identifier type display."
    )
    patient_identifier_type_user_selected: bool | None = Field(
        None, description="Patient identifier type user selected."
    )
    patient_identifier_type_text: str | None = Field(
        None, description="Patient identifier type text."
    )
    patient_identifier_system: str | None = Field(
        None, description="Patient identifier system."
    )
    patient_identifier_value: str | None = Field(
        None, description="Patient identifier value."
    )
    patient_identifier_period_start: datetime | None = Field(
        None, description="Patient identifier period start."
    )
    patient_identifier_period_end: datetime | None = Field(
        None, description="Patient identifier period end."
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

    @model_validator(mode="after")
    def validate_patient(self) -> "RelatedPersonCreateSchema":
        has_ref = bool(self.patient)
        has_ident = any(
            getattr(self, f"patient_{suffix}") is not None
            for suffix in _IDENTIFIER_FALLBACK_SUFFIXES
        )
        has_display = bool(self.patient_display)
        if not (has_ref or has_ident or has_display):
            raise ValueError(
                "Either patient (reference URL) or at least one patient_identifier_* field or patient_display must be provided."
            )
        return self


class RelatedPersonPatchSchema(BaseModel):
    """Request body for PATCH /api/fhir/v1/related_persons/{id}.

    All fields optional; omitted fields are unchanged; supplied sub-resource lists replace wholesale.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "active": False,
            }
        },
    )

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
    patient_identifier_use: IdentifierUse | None = Field(
        None, description="Patient identifier use."
    )
    patient_identifier_type_system: str | None = Field(
        None, description="Patient identifier type system."
    )
    patient_identifier_type_version: str | None = Field(
        None, description="Patient identifier type version."
    )
    patient_identifier_type_code: str | None = Field(
        None, description="Patient identifier type code."
    )
    patient_identifier_type_display: str | None = Field(
        None, description="Patient identifier type display."
    )
    patient_identifier_type_user_selected: bool | None = Field(
        None, description="Patient identifier type user selected."
    )
    patient_identifier_type_text: str | None = Field(
        None, description="Patient identifier type text."
    )
    patient_identifier_system: str | None = Field(
        None, description="Patient identifier system."
    )
    patient_identifier_value: str | None = Field(
        None, description="Patient identifier value."
    )
    patient_identifier_period_start: datetime | None = Field(
        None, description="Patient identifier period start."
    )
    patient_identifier_period_end: datetime | None = Field(
        None, description="Patient identifier period end."
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
