from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput
from app.schemas.enums import AdministrativeGender, IdentifierUse

from .address import PatientAddressInput
from .communication import PatientCommunicationInput
from .contact import PatientContactInput
from .general_practitioner import PatientGeneralPractitionerInput
from .identifier import PatientIdentifierInput
from .link import PatientLinkInput
from .name import PatientNameInput
from .photo import PatientPhotoInput
from .telecom import PatientTelecomInput


class PatientCreateSchema(BaseModel):
    """Creates a Patient and any combination of its sub-resources atomically in one
    request. `tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) —
    neither is a request body field. Patient keeps a plain `user_id` field: a Patient record
    is scoped to an individual end-user's account."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-abc123",
                "active": True,
                "gender": "female",
                "birth_date": "1990-07-22",
                "deceased_boolean": False,
                "marital_status_text": "Never Married",
                "marital_status_coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                        "code": "S",
                        "display": "Never Married",
                    }
                ],
                "managing_organization": "Organization/190001",
                "managing_organization_display": "Sunrise Medical Center",
                "name": [
                    {
                        "use": "official",
                        "family": "Carter",
                        "given": ["Emily", "Rose"],
                    }
                ],
                "identifier": [
                    {
                        "use": "official",
                        "system": "http://hospital.example.com/mrn",
                        "value": "MRN-200456",
                        "type_coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "MR",
                                "display": "Medical record number",
                            }
                        ],
                    }
                ],
                "telecom": [
                    {"system": "phone", "value": "+1-555-321-7890", "use": "mobile", "rank": 1},
                    {"system": "email", "value": "emily.carter@example.com", "use": "home", "rank": 2},
                ],
                "address": [
                    {
                        "use": "home",
                        "type": "both",
                        "line": ["12 Birch Lane"],
                        "city": "Cambridge",
                        "state": "MA",
                        "postal_code": "02139",
                        "country": "US",
                    }
                ],
                "photo": [
                    {
                        "content_type": "image/jpeg",
                        "url": "https://example.com/patients/photos/emily-carter.jpg",
                        "title": "Profile photo",
                    }
                ],
                "contact": [
                    {
                        "relationship": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/v2-0131",
                                        "code": "N",
                                        "display": "Next-of-Kin",
                                    }
                                ]
                            }
                        ],
                        "name_family": "Carter",
                        "name_given": ["Michael"],
                        "telecom": [
                            {"system": "phone", "value": "+1-555-654-3210", "use": "mobile"}
                        ],
                        "gender": "male",
                    }
                ],
                "communication": [
                    {
                        "language_coding": [
                            {"system": "urn:ietf:bcp:47", "code": "en", "display": "English"}
                        ],
                        "preferred": True,
                    }
                ],
                "general_practitioner": [
                    {
                        "reference": "Practitioner/30001",
                        "display": "Dr. Priya R. Sharma",
                    }
                ],
                "link": [
                    {
                        "other": "RelatedPerson/300001",
                        "other_display": "Michael Carter (spouse)",
                        "type": "seealso",
                    }
                ],
            }
        },
    )

    user_id: str | None = Field(
        None, description="Gateway-forwarded acting end-user's own account ID."
    )
    active: bool | None = Field(
        None, description="Whether this patient's record is in active use."
    )
    gender: AdministrativeGender | None = Field(
        None, description="Administrative Gender — male|female|other|unknown."
    )
    birth_date: date | None = Field(None, description="Date of birth for the individual.")
    deceased_boolean: bool | None = Field(
        None, description="Indicates if the individual is deceased."
    )
    deceased_date_time: datetime | None = Field(
        None, description="The date and time when the individual died."
    )
    marital_status_text: str | None = Field(
        None, description="Marital status narrative representation."
    )
    marital_status_coding: list[CodingInput] | None = Field(
        None, description="Coding(s) for the marital status."
    )
    multiple_birth_boolean: bool | None = Field(
        None, description="Whether patient is part of a multiple birth."
    )
    multiple_birth_integer: int | None = Field(
        None, description="Birth order in a multiple birth."
    )
    managing_organization: str | None = Field(
        None,
        description="Organization that is custodian of the patient record (e.g. 'Organization/190001').",
    )
    managing_organization_display: str | None = Field(
        None, description="Display narrative for the managing organization reference."
    )
    managing_organization_identifier_system: str | None = Field(
        None, description="Logical-reference fallback — identifier namespace URL."
    )
    managing_organization_identifier_value: str | None = Field(
        None, description="Logical-reference fallback — identifier value."
    )
    managing_organization_identifier_use: IdentifierUse | None = Field(
        None, description="Logical-reference fallback — identifier use."
    )
    managing_organization_identifier_type_text: str | None = Field(
        None, description="Logical-reference fallback — identifier type text."
    )

    identifier: list[PatientIdentifierInput] | None = Field(
        None, description="An identifier for this patient."
    )
    name: list[PatientNameInput] | None = Field(
        None, description="A name associated with the patient."
    )
    telecom: list[PatientTelecomInput] | None = Field(
        None, description="A contact detail for the individual."
    )
    address: list[PatientAddressInput] | None = Field(
        None, description="An address for the individual."
    )
    photo: list[PatientPhotoInput] | None = Field(
        None, description="Image of the patient."
    )
    contact: list[PatientContactInput] | None = Field(
        None, description="A contact party (e.g. guardian, partner, friend) for the patient."
    )
    communication: list[PatientCommunicationInput] | None = Field(
        None, description="A language which may be used to communicate with the patient."
    )
    general_practitioner: list[PatientGeneralPractitionerInput] | None = Field(
        None, description="Patient's nominated care provider."
    )
    link: list[PatientLinkInput] | None = Field(
        None, description="Link to a Patient or RelatedPerson resource that concerns the same actual individual."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries.",
    )


class PatientPatchSchema(BaseModel):
    """Partial update — only supplied fields are written. Every supplied
    sub-resource list (even `[]`) replaces the corresponding rows wholesale;
    omitted lists are left untouched. `updated_by` comes from the verified JWT (`actor.sub`),
    not a request body field. `user_id` is immutable after create — excluded here."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "active": False,
                "gender": "female",
            }
        },
    )

    active: bool | None = Field(
        None, description="Whether this patient's record is in active use."
    )
    gender: AdministrativeGender | None = Field(
        None, description="Administrative Gender — male|female|other|unknown."
    )
    birth_date: date | None = Field(None, description="Date of birth for the individual.")
    deceased_boolean: bool | None = Field(
        None, description="Indicates if the individual is deceased."
    )
    deceased_date_time: datetime | None = Field(
        None, description="The date and time when the individual died."
    )
    marital_status_text: str | None = Field(
        None, description="Marital status narrative representation."
    )
    marital_status_coding: list[CodingInput] | None = Field(
        None, description="Coding(s) for the marital status — replaces the list if supplied."
    )
    multiple_birth_boolean: bool | None = Field(
        None, description="Whether patient is part of a multiple birth."
    )
    multiple_birth_integer: int | None = Field(
        None, description="Birth order in a multiple birth."
    )
    managing_organization: str | None = Field(
        None,
        description="Organization that is custodian of the patient record (e.g. 'Organization/190001').",
    )
    managing_organization_display: str | None = Field(
        None, description="Display narrative for the managing organization reference."
    )
    managing_organization_identifier_system: str | None = Field(
        None, description="Logical-reference fallback — identifier namespace URL."
    )
    managing_organization_identifier_value: str | None = Field(
        None, description="Logical-reference fallback — identifier value."
    )
    managing_organization_identifier_use: IdentifierUse | None = Field(
        None, description="Logical-reference fallback — identifier use."
    )
    managing_organization_identifier_type_text: str | None = Field(
        None, description="Logical-reference fallback — identifier type text."
    )

    identifier: list[PatientIdentifierInput] | None = Field(
        None, description="An identifier for this patient — replaces the full list if supplied."
    )
    name: list[PatientNameInput] | None = Field(
        None, description="A name associated with the patient — replaces the full list if supplied."
    )
    telecom: list[PatientTelecomInput] | None = Field(
        None, description="A contact detail for the individual — replaces the full list if supplied."
    )
    address: list[PatientAddressInput] | None = Field(
        None, description="An address for the individual — replaces the full list if supplied."
    )
    photo: list[PatientPhotoInput] | None = Field(
        None, description="Image of the patient — replaces the full list if supplied."
    )
    contact: list[PatientContactInput] | None = Field(
        None, description="A contact party for the patient — replaces the full list if supplied."
    )
    communication: list[PatientCommunicationInput] | None = Field(
        None, description="A language which may be used to communicate with the patient — replaces the full list if supplied."
    )
    general_practitioner: list[PatientGeneralPractitionerInput] | None = Field(
        None, description="Patient's nominated care provider — replaces the full list if supplied."
    )
    link: list[PatientLinkInput] | None = Field(
        None, description="Link to a Patient or RelatedPerson resource — replaces the full list if supplied."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries — replaces the full list if supplied.",
    )
