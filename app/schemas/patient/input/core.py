from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IdentifierUse
from app.models.patient.enums import PatientGender

from .address import AddressCreate
from .communication import CommunicationCreate
from .contact import ContactCreate
from .general_practitioner import GeneralPractitionerCreate
from .identifier import IdentifierCreate
from .link import LinkCreate
from .name import NameCreate
from .photo import PhotoCreate
from .telecom import TelecomCreate

# ── Patient create / patch ─────────────────────────────────────────────────────


class PatientCreateSchema(BaseModel):
    """Core scalar fields for creating a FHIR R4 Patient resource. Sub-resource
    arrays (name, identifier, telecom, etc.) are added via dedicated endpoints —
    see PatientFullCreateSchema to create everything in one request."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-uuid-123",
                "active": True,
                "gender": "male",
                "birth_date": "1985-04-12",
                "deceased_boolean": False,
                "marital_status_code": "M",
                "marital_status_system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                "marital_status_display": "Married",
            }
        },
    )

    user_id: str | None = Field(
        None,
        description="Gateway-forwarded ID of the user who owns this record (JWT sub). Describes who this Patient record belongs to — not a field of the FHIR Patient resource's own clinical content.",
    )
    active: bool | None = Field(
        True, description="Whether this patient's record is in active use."
    )
    gender: PatientGender | None = Field(
        None, description="Administrative gender. male|female|other|unknown."
    )
    birth_date: date | None = Field(
        None, description="The date of birth for the individual."
    )
    deceased_boolean: bool | None = Field(
        None,
        description="deceased[x] choice — indicates the individual is deceased (boolean form).",
    )
    deceased_datetime: datetime | None = Field(
        None,
        description="deceased[x] choice — the date/time the individual died (dateTime form).",
    )
    marital_status_system: str | None = Field(
        None,
        description="maritalStatus.coding.system — coding system for the patient's marital status.",
    )
    marital_status_version: str | None = Field(
        None,
        description="maritalStatus.coding.version — version of the marital-status coding system.",
    )
    marital_status_code: str | None = Field(
        None,
        description="maritalStatus.coding.code — code for the patient's marital (civil) status.",
    )
    marital_status_display: str | None = Field(
        None,
        description="maritalStatus.coding.display — human-readable display for the marital-status code.",
    )
    marital_status_text: str | None = Field(
        None,
        description="maritalStatus.text — plain-text rendering of the marital status.",
    )
    marital_status_user_selected: bool | None = Field(
        None,
        description="maritalStatus.coding.userSelected — whether this coding was chosen directly by the user.",
    )
    multiple_birth_boolean: bool | None = Field(
        None,
        description="multipleBirth[x] choice — whether the patient is part of a multiple birth (boolean form).",
    )
    multiple_birth_integer: int | None = Field(
        None,
        description="multipleBirth[x] choice — the patient's birth order in a multiple birth (integer form).",
    )
    managing_organization: str | None = Field(
        None,
        description=(
            "managingOrganization — Reference(Organization) that is the custodian of "
            "the patient record, as a FHIR reference string, e.g. 'Organization/100'."
        ),
    )
    managing_organization_display: str | None = Field(
        None,
        description="managingOrganization.display — display text for the managing organization.",
    )
    managing_organization_identifier_use: IdentifierUse | None = Field(
        None,
        description="Fallback identifier (used when the managing organization "
        "isn't a resource in this system) — usual|official|temp|secondary|old.",
    )
    managing_organization_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    managing_organization_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    managing_organization_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type (e.g. MR, SS)."
    )
    managing_organization_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    managing_organization_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    managing_organization_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    managing_organization_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    managing_organization_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    managing_organization_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — when it became valid."
    )
    managing_organization_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — when it stopped being valid."
    )


class PatientPatchSchema(BaseModel):
    """Partial update to a Patient's core scalar fields. Only supplied fields are
    written; sub-resources are managed via dedicated endpoints."""

    model_config = ConfigDict(extra="forbid")

    active: bool | None = Field(
        None, description="Whether this patient's record is in active use."
    )
    gender: PatientGender | None = Field(None, description="male|female|other|unknown.")
    birth_date: date | None = Field(
        None, description="The date of birth for the individual."
    )
    deceased_boolean: bool | None = Field(
        None,
        description="deceased[x] choice — indicates the individual is deceased (boolean form).",
    )
    deceased_datetime: datetime | None = Field(
        None,
        description="deceased[x] choice — the date/time the individual died (dateTime form).",
    )
    marital_status_system: str | None = Field(
        None, description="Coding system for the patient's marital status."
    )
    marital_status_version: str | None = Field(
        None, description="Version of the marital-status coding system."
    )
    marital_status_code: str | None = Field(
        None, description="Code for the patient's marital (civil) status."
    )
    marital_status_display: str | None = Field(
        None, description="Display for the marital-status code."
    )
    marital_status_text: str | None = Field(
        None, description="Plain-text rendering of the marital status."
    )
    marital_status_user_selected: bool | None = Field(
        None, description="Whether this coding was chosen directly by the user."
    )
    multiple_birth_boolean: bool | None = Field(
        None,
        description="Whether the patient is part of a multiple birth (boolean form).",
    )
    multiple_birth_integer: int | None = Field(
        None,
        description="The patient's birth order in a multiple birth (integer form).",
    )
    managing_organization: str | None = Field(
        None, description="FHIR reference, e.g. 'Organization/100'."
    )
    managing_organization_display: str | None = Field(
        None, description="Display text for the managing organization."
    )
    managing_organization_identifier_use: IdentifierUse | None = Field(
        None,
        description="Fallback identifier (used when the managing organization "
        "isn't a resource in this system) — usual|official|temp|secondary|old.",
    )
    managing_organization_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    managing_organization_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    managing_organization_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type (e.g. MR, SS)."
    )
    managing_organization_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    managing_organization_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    managing_organization_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    managing_organization_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    managing_organization_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    managing_organization_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — when it became valid."
    )
    managing_organization_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — when it stopped being valid."
    )


class PatientFullCreateSchema(PatientCreateSchema):
    """Creates a Patient and any combination of sub-resources atomically in a
    single DB transaction. All sub-resource lists are optional."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-uuid-123",
                "active": True,
                "gender": "male",
                "birth_date": "1985-04-12",
                "names": [{"use": "official", "family": "Doe", "given": ["John"]}],
                "identifiers": [
                    {"value": "MRN-123456", "system": "http://hospital.com/mrn"}
                ],
                "telecom": [
                    {"system": "phone", "value": "+1-555-123-4567", "use": "mobile"}
                ],
                "addresses": [
                    {"use": "home", "city": "New York", "state": "NY", "country": "USA"}
                ],
                "communications": [{"language_code": "en", "preferred": True}],
            }
        },
    )
    names: list[NameCreate] | None = Field(
        None, description="HumanName entries for the patient."
    )
    identifiers: list[IdentifierCreate] | None = Field(
        None,
        description="Business identifiers (MRN, SSN, passport, etc.) for the patient.",
    )
    telecom: list[TelecomCreate] | None = Field(
        None, description="Contact points (phone, email, etc.) for the patient."
    )
    addresses: list[AddressCreate] | None = Field(
        None, description="Addresses for the patient."
    )
    photos: list[PhotoCreate] | None = Field(
        None, description="Image attachments of the patient."
    )
    contacts: list[ContactCreate] | None = Field(
        None,
        description="Contact parties (guardian, next-of-kin, emergency contact) for the patient.",
    )
    communications: list[CommunicationCreate] | None = Field(
        None,
        description="Languages the patient can use for healthcare-related communication.",
    )
    general_practitioners: list[GeneralPractitionerCreate] | None = Field(
        None,
        description="References to the patient's nominated primary care provider(s).",
    )
    links: list[LinkCreate] | None = Field(
        None,
        description="Links to other Patient/RelatedPerson resources concerning the same actual person.",
    )


class PatientFullPatchSchema(PatientPatchSchema):
    """Patches a Patient's scalar fields and, for each sub-resource list that is
    supplied (even `[]`), atomically replaces it. Lists that are omitted are left
    untouched."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "active": True,
                "gender": "male",
                "names": [{"use": "official", "family": "Doe", "given": ["John"]}],
                "telecom": [
                    {"system": "phone", "value": "+1-555-999-0000", "use": "mobile"}
                ],
                "communications": [{"language_code": "en", "preferred": True}],
            }
        },
    )
    names: list[NameCreate] | None = Field(
        None,
        description="HumanName entries for the patient — replaces the full list if supplied.",
    )
    identifiers: list[IdentifierCreate] | None = Field(
        None,
        description="Business identifiers for the patient — replaces the full list if supplied.",
    )
    telecom: list[TelecomCreate] | None = Field(
        None,
        description="Contact points for the patient — replaces the full list if supplied.",
    )
    addresses: list[AddressCreate] | None = Field(
        None,
        description="Addresses for the patient — replaces the full list if supplied.",
    )
    photos: list[PhotoCreate] | None = Field(
        None,
        description="Image attachments of the patient — replaces the full list if supplied.",
    )
    contacts: list[ContactCreate] | None = Field(
        None,
        description="Contact parties for the patient — replaces the full list if supplied.",
    )
    communications: list[CommunicationCreate] | None = Field(
        None,
        description="Communication languages for the patient — replaces the full list if supplied.",
    )
    general_practitioners: list[GeneralPractitionerCreate] | None = Field(
        None,
        description="General-practitioner references — replaces the full list if supplied.",
    )
    links: list[LinkCreate] | None = Field(
        None, description="Patient links — replaces the full list if supplied."
    )
