from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import AdministrativeGender

from .address import PractitionerAddressInput
from .communication import PractitionerCommunicationInput
from .identifier import PractitionerIdentifierInput
from .name import PractitionerNameInput
from .photo import PractitionerPhotoInput
from .qualification import PractitionerQualificationInput
from .telecom import PractitionerTelecomInput


class PractitionerCreateSchema(BaseModel):
    """Creates a Practitioner and any combination of its sub-resources
    (identifier, name, telecom, address, photo, qualification,
    communication) atomically in one request — same single-endpoint shape
    as Organization/Location/HealthcareService, see
    OrganizationCreateSchema's docstring. `tenant_id`/`created_by` both come
    from the verified JWT (`actor.org_id`/`actor.sub`) — neither is a
    request body field. Unlike Organization/Location/HealthcareService,
    Practitioner keeps a plain `user_id` field: a Practitioner record is
    naturally scoped to an individual end-user's own account (the
    clinician), not a shared tenant-level entity — see PractitionerModel's
    docstring (app/models/practitioner/core.py)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-abc123",
                "active": True,
                "gender": "female",
                "birth_date": "1980-05-15",
                "identifier": [
                    {
                        "value": "9941339108",
                        "system": "http://hl7.org/fhir/sid/us-npi",
                        "use": "official",
                    }
                ],
                "name": [
                    {
                        "use": "official",
                        "family": "Careful",
                        "given": ["Adam"],
                        "prefix": ["Dr"],
                    }
                ],
                "telecom": [{"system": "phone", "value": "555-9988", "use": "work"}],
                "address": [
                    {
                        "use": "work",
                        "line": ["534 Erewhon St"],
                        "city": "PleasantVille",
                        "state": "Vic",
                        "postal_code": "3999",
                    }
                ],
                "qualification": [
                    {
                        "code_coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0360/2.7",
                                "code": "BS",
                                "display": "Bachelor of Science",
                            }
                        ],
                        "issuer": "Organization/190001",
                    }
                ],
                "communication": [
                    {
                        "coding": [
                            {
                                "system": "urn:ietf:bcp:47",
                                "code": "en",
                                "display": "English",
                            }
                        ]
                    }
                ],
            }
        },
    )

    user_id: str | None = Field(
        None, description="Gateway-forwarded acting end-user's own account ID."
    )

    # active (0..1) — R4 removed the R3 default of true; no default here either.
    active: bool | None = Field(
        None, description="Whether this practitioner's record is in active use."
    )
    gender: AdministrativeGender | None = Field(
        None, description="male|female|other|unknown."
    )
    birth_date: date | None = Field(None, description="Date of birth.")

    identifier: list[PractitionerIdentifierInput] | None = Field(
        None, description="Identifiers for the person in this role."
    )
    name: list[PractitionerNameInput] | None = Field(
        None, description="Name(s) associated with the practitioner."
    )
    telecom: list[PractitionerTelecomInput] | None = Field(
        None, description="Contact details applying to all roles."
    )
    address: list[PractitionerAddressInput] | None = Field(
        None, description="Non-role-specific addresses, typically home."
    )
    photo: list[PractitionerPhotoInput] | None = Field(
        None, description="Image(s) of the person."
    )
    qualification: list[PractitionerQualificationInput] | None = Field(
        None, description="Certifications, licenses, or training."
    )
    communication: list[PractitionerCommunicationInput] | None = Field(
        None, description="Languages the practitioner can use in patient communication."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries. Not yet validated against registered extension definitions.",
    )


class PractitionerPatchSchema(BaseModel):
    """Partial update — only supplied fields are written. Every supplied
    sub-resource list (even `[]`) replaces the corresponding rows wholesale;
    omitted lists are left untouched — see OrganizationPatchSchema's
    docstring. `updated_by` comes from the verified JWT (`actor.sub`), not a
    request body field. `user_id` is immutable after create — excluded
    here, same as `tenant_id`."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "active": False,
                "name": [{"use": "official", "family": "Careful", "given": ["Adam"]}],
            }
        },
    )

    active: bool | None = Field(
        None, description="Whether this practitioner's record is in active use."
    )
    gender: AdministrativeGender | None = Field(
        None, description="male|female|other|unknown."
    )
    birth_date: date | None = Field(None, description="Date of birth.")

    identifier: list[PractitionerIdentifierInput] | None = Field(
        None,
        description="Identifiers for the person in this role — replaces the full list if supplied.",
    )
    name: list[PractitionerNameInput] | None = Field(
        None,
        description="Name(s) associated with the practitioner — replaces the full list if supplied.",
    )
    telecom: list[PractitionerTelecomInput] | None = Field(
        None,
        description="Contact detail(s) applying to all roles — replaces the full list if supplied.",
    )
    address: list[PractitionerAddressInput] | None = Field(
        None,
        description="Address(es), typically home — replaces the full list if supplied.",
    )
    photo: list[PractitionerPhotoInput] | None = Field(
        None, description="Image(s) of the person — replaces the full list if supplied."
    )
    qualification: list[PractitionerQualificationInput] | None = Field(
        None,
        description="Certification(s), license(s), or training — replaces the full list if supplied.",
    )
    communication: list[PractitionerCommunicationInput] | None = Field(
        None,
        description="Language(s) the practitioner can use in patient communication — replaces the full list if supplied.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries — replaces the full list if supplied.",
    )
