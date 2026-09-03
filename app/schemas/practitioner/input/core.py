from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import AdministrativeGender

from .address import PractitionerAddressCreate
from .communication import PractitionerCommunicationCreate
from .identifier import PractitionerIdentifierCreate
from .name import PractitionerNameCreate
from .photo import PractitionerPhotoCreate
from .qualification import PractitionerQualificationCreate
from .telecom import PractitionerTelecomCreate

# ── Practitioner create / patch ────────────────────────────────────────────────


class PractitionerCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-uuid-123",
                "active": True,
                "gender": "female",
                "birth_date": "1978-03-15",
            }
        },
    )

    user_id: str | None = Field(
        None,
        description="Gateway-forwarded ID of the user who owns this record (JWT sub). Describes who this Practitioner record belongs to — not a field of the FHIR Practitioner resource's own clinical content.",
    )
    active: bool | None = Field(
        False, description="Whether this practitioner's record is in active use."
    )
    gender: AdministrativeGender = Field(
        ...,
        description="Administrative Gender — the gender that the person is considered to have for administration and record keeping purposes. male|female|other|unknown.",
    )
    birth_date: date = Field(..., description="The date of birth for the practitioner.")


class PractitionerPatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    active: bool | None = Field(
        None, description="Whether this practitioner's record is in active use."
    )
    gender: AdministrativeGender | None = Field(
        None,
        description="Administrative Gender — the gender that the person is considered to have for administration and record keeping purposes. male|female|other|unknown.",
    )
    birth_date: date | None = Field(
        None, description="The date of birth for the practitioner."
    )


class PractitionerFullCreateSchema(PractitionerCreateSchema):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-uuid-123",
                "active": True,
                "gender": "female",
                "birth_date": "1978-03-15",
                "names": [{"use": "official", "family": "Smith", "given": ["Jane"]}],
                "identifiers": [
                    {"system": "http://hl7.org/fhir/sid/us-npi", "value": "1234567890"}
                ],
                "telecom": [
                    {
                        "system": "email",
                        "value": "jane.smith@hospital.org",
                        "use": "work",
                    }
                ],
                "qualifications": [
                    {
                        "code_code": "MD",
                        "code_display": "Doctor of Medicine",
                        "period_start": "2005-06-01",
                    }
                ],
                "communications": [
                    {
                        "language_system": "urn:ietf:bcp:47",
                        "language_code": "en",
                        "language_display": "English",
                    }
                ],
            }
        },
    )
    names: list[PractitionerNameCreate] | None = None
    identifiers: list[PractitionerIdentifierCreate] | None = None
    telecom: list[PractitionerTelecomCreate] | None = None
    addresses: list[PractitionerAddressCreate] | None = None
    photos: list[PractitionerPhotoCreate] | None = None
    qualifications: list[PractitionerQualificationCreate] | None = None
    communications: list[PractitionerCommunicationCreate] | None = None


class PractitionerFullPatchSchema(PractitionerPatchSchema):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "active": True,
                "gender": "female",
                "names": [{"use": "official", "family": "Smith", "given": ["Jane"]}],
                "telecom": [
                    {
                        "system": "email",
                        "value": "jane.smith@hospital.org",
                        "use": "work",
                    }
                ],
                "qualifications": [
                    {"code_code": "MD", "code_display": "Doctor of Medicine"}
                ],
                "communications": [
                    {
                        "language_system": "urn:ietf:bcp:47",
                        "language_code": "en",
                        "language_display": "English",
                    }
                ],
            }
        },
    )
    names: list[PractitionerNameCreate] | None = None
    identifiers: list[PractitionerIdentifierCreate] | None = None
    telecom: list[PractitionerTelecomCreate] | None = None
    addresses: list[PractitionerAddressCreate] | None = None
    photos: list[PractitionerPhotoCreate] | None = None
    qualifications: list[PractitionerQualificationCreate] | None = None
    communications: list[PractitionerCommunicationCreate] | None = None
