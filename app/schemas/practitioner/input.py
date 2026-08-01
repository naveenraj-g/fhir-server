from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import (
    AddressType,
    AddressUse,
    AdministrativeGender,
    ContactPointSystem,
    ContactPointUse,
    HumanNameUse,
    IdentifierUse,
)

# ── Sub-resource create schemas ────────────────────────────────────────────────


class PractitionerNameCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: HumanNameUse | None = Field(
        None,
        description="Identifies the purpose for this name. usual|official|temp|nickname|anonymous|old|maiden.",
    )
    text: str | None = Field(None, description="Full name as a display string.")
    family: str | None = Field(None, description="Family (last) name.")
    given: list[str] | None = Field(None, description="Given (first/middle) names.")
    prefix: list[str] | None = Field(
        None, description="Name prefixes (Mr., Dr., etc.)."
    )
    suffix: list[str] | None = Field(None, description="Name suffixes (Jr., MD, etc.).")
    period_start: datetime | None = Field(
        None, description="Start of the period during which this name was valid."
    )
    period_end: datetime | None = Field(
        None, description="End of the period during which this name was valid."
    )


class PractitionerIdentifierCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: IdentifierUse | None = Field(
        None,
        description="Identifies the purpose for this identifier, if known. usual|official|temp|secondary|old.",
    )
    type_system: str | None = Field(
        None, description="Coding system for identifier type."
    )
    type_version: str | None = Field(
        None, description="Version of the coding system for identifier type."
    )
    type_code: str | None = Field(
        None, description="Code for identifier type (e.g. NPI, DEA, license)."
    )
    type_display: str | None = Field(None, description="Display for identifier type.")
    type_text: str | None = Field(
        None, description="Plain-text description of identifier type."
    )
    type_user_selected: bool | None = Field(
        None,
        description="Whether this identifier-type coding was chosen directly by the user.",
    )
    system: str = Field(
        ...,
        description="Establishes the namespace for the value (e.g. NPI system) — that is, a URL that describes a set of unique values.",
    )
    value: str = Field(
        ..., description="Identifier value (e.g. NPI number, license number)."
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the period during which this identifier is/was valid for use.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period during which this identifier is/was valid for use.",
    )
    assigner: str | None = Field(
        None,
        description="Reference(Organization) that issued this identifier, as a FHIR reference string (e.g. 'Organization/100').",
    )
    assigner_display: str | None = Field(
        None, description="Display name of the organization that issued the identifier."
    )
    assigner_identifier_use: IdentifierUse | None = Field(
        None,
        description="Fallback identifier (used when the assigning organization isn't a resource in this system) — usual|official|temp|secondary|old.",
    )
    assigner_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    assigner_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    assigner_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    assigner_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    assigner_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    assigner_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    assigner_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    assigner_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    assigner_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    assigner_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of validity period."
    )


class PractitionerTelecomCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    system: ContactPointSystem = Field(
        ...,
        description="Telecommunications form for this contact point — what communications system is required to make use of it. phone|fax|email|pager|url|sms|other.",
    )
    value: str = Field(
        ..., description="Contact value (phone number, email address, etc.)."
    )
    use: ContactPointUse | None = Field(
        None,
        description="Identifies the purpose for the contact point. home|work|temp|old|mobile.",
    )
    rank: int | None = Field(
        None,
        ge=1,
        description="Specifies a preferred order in which to use a set of contacts. Lower values are more preferred than higher values.",
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the period during which this contact point was/is in use.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period during which this contact point was/is in use.",
    )


class PractitionerAddressCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: AddressUse | None = Field(
        None, description="The purpose of this address. home|work|temp|old|billing."
    )
    type: AddressType = Field(
        ...,
        description="Distinguishes between physical addresses (those you can visit) and mailing addresses. postal|physical|both.",
    )
    text: str | None = Field(None, description="Full address as plain text.")
    line: list[str] | None = Field(None, description="Street address lines.")
    city: str = Field(..., description="City, town, or suburb.")
    district: str | None = Field(
        None, description="The name of the administrative area (county)."
    )
    state: str = Field(..., description="State, province, or region.")
    postal_code: str = Field(..., description="Postal or ZIP code.")
    country: str = Field(..., description="Country.")
    period_start: datetime | None = Field(
        None, description="Start of the period during which this address was/is in use."
    )
    period_end: datetime | None = Field(
        None, description="End of the period during which this address was/is in use."
    )


class PractitionerPhotoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content_type: str | None = Field(None, description="MIME type (e.g. image/png).")
    language: str | None = Field(None, description="BCP-47 language code.")
    data: str | None = Field(None, description="Base64-encoded image data.")
    url: str = Field(..., description="URL where the image can be retrieved.")
    size: int | None = Field(None, description="Size in bytes before base64 encoding.")
    hash: str | None = Field(None, description="Base64-encoded SHA-1 hash of the data.")
    title: str | None = Field(None, description="Label or display title.")
    creation: datetime | None = Field(None, description="When the image was created.")


class QualificationIdentifierCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: IdentifierUse | None = Field(
        None,
        description="Identifies the purpose for this identifier, if known. usual|official|temp|secondary|old.",
    )
    type_system: str | None = Field(
        None, description="Coding system for identifier type."
    )
    type_version: str | None = Field(
        None, description="Version of the coding system for identifier type."
    )
    type_code: str | None = Field(None, description="Code for identifier type.")
    type_display: str | None = Field(None, description="Display for identifier type.")
    type_text: str | None = Field(
        None, description="Plain-text description of identifier type."
    )
    type_user_selected: bool | None = Field(
        None,
        description="Whether this identifier-type coding was chosen directly by the user.",
    )
    system: str = Field(
        ..., description="Namespace URI for the qualification identifier."
    )
    value: str = Field(..., description="Qualification or license number.")
    period_start: datetime | None = Field(
        None,
        description="Start of the period during which this identifier is/was valid for use.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period during which this identifier is/was valid for use.",
    )
    assigner: str | None = Field(
        None,
        description="Reference(Organization) that issued this identifier, as a FHIR reference string (e.g. 'Organization/100').",
    )
    assigner_display: str | None = Field(
        None, description="Display name of the issuing organization."
    )
    assigner_identifier_use: IdentifierUse | None = Field(
        None,
        description="Fallback identifier (used when the assigning organization isn't a resource in this system) — usual|official|temp|secondary|old.",
    )
    assigner_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    assigner_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    assigner_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    assigner_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    assigner_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    assigner_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    assigner_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    assigner_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    assigner_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    assigner_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of validity period."
    )


class PractitionerQualificationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identifier: list[QualificationIdentifierCreate] | None = Field(
        None, description="Identifiers for this qualification (e.g. license numbers)."
    )
    code_system: str | None = Field(
        None,
        description="Coding system for the qualification type (e.g. http://snomed.info/sct).",
    )
    code_code: str | None = Field(
        None, description="Coded qualification type (e.g. '394814009')."
    )
    code_display: str | None = Field(
        None, description="Display for the qualification code."
    )
    code_text: str | None = Field(
        None,
        description="Human-readable qualification type, e.g. 'MD - Doctor of Medicine'.",
    )
    status_system: str | None = Field(
        None, description="Coding system for qualification status."
    )
    status_code: str | None = Field(
        None, description="Status code (e.g. active, inactive, pending)."
    )
    status_display: str | None = Field(None, description="Display for the status code.")
    status_text: str | None = Field(
        None, description="Human-readable qualification status."
    )
    period_start: datetime | None = Field(
        None, description="Start of the period during which the qualification is valid."
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period during which the qualification is valid (expiry).",
    )
    issuer: str | None = Field(
        None,
        description="FHIR reference to the issuing organization, e.g. 'Organization/100'.",
    )
    issuer_display: str | None = Field(
        None, description="Display name of the issuing organization."
    )
    issuer_identifier_use: IdentifierUse | None = Field(
        None,
        description="Fallback identifier (used when the issuing organization isn't a resource in this system) — usual|official|temp|secondary|old.",
    )
    issuer_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    issuer_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    issuer_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    issuer_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    issuer_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    issuer_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    issuer_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    issuer_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    issuer_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    issuer_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of validity period."
    )


class PractitionerCommunicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language_system: str = Field(..., description="URI of the language code system.")
    language_version: str | None = Field(
        None, description="Version of the language code system."
    )
    language_code: str = Field(
        ..., description="ISO-639-1 language code (e.g. en, fr, de)."
    )
    language_display: str = Field(
        ..., description="Human-readable display for the language."
    )
    language_text: str | None = None
    language_user_selected: bool | None = Field(
        None,
        description="Whether this language coding was chosen directly by the user.",
    )


# ── Sub-resource patch schemas ────────────────────────────────────────────────


class PractitionerNamePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: HumanNameUse | None = None
    text: str | None = None
    family: str | None = None
    given: list[str] | None = None
    prefix: list[str] | None = None
    suffix: list[str] | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None


class PractitionerIdentifierPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: IdentifierUse | None = None
    type_system: str | None = None
    type_version: str | None = None
    type_code: str | None = None
    type_display: str | None = None
    type_text: str | None = None
    type_user_selected: bool | None = None
    system: str | None = None
    value: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    assigner: str | None = None
    assigner_display: str | None = None
    assigner_identifier_use: IdentifierUse | None = None
    assigner_identifier_type_system: str | None = None
    assigner_identifier_type_version: str | None = None
    assigner_identifier_type_code: str | None = None
    assigner_identifier_type_display: str | None = None
    assigner_identifier_type_text: str | None = None
    assigner_identifier_type_user_selected: bool | None = None
    assigner_identifier_system: str | None = None
    assigner_identifier_value: str | None = None
    assigner_identifier_period_start: datetime | None = None
    assigner_identifier_period_end: datetime | None = None


class PractitionerTelecomPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    system: ContactPointSystem | None = None
    value: str | None = None
    use: ContactPointUse | None = None
    rank: int | None = Field(None, ge=1)
    period_start: datetime | None = None
    period_end: datetime | None = None


class PractitionerAddressPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: AddressUse | None = None
    type: AddressType | None = None
    text: str | None = None
    line: list[str] | None = None
    city: str | None = None
    district: str | None = Field(
        None, description="The name of the administrative area (county)."
    )
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None


class PractitionerPhotoPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content_type: str | None = None
    language: str | None = None
    data: str | None = None
    url: str | None = None
    size: int | None = None
    hash: str | None = None
    title: str | None = None
    creation: datetime | None = None


class QualificationIdentifierPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: IdentifierUse | None = None
    type_system: str | None = None
    type_version: str | None = None
    type_code: str | None = None
    type_display: str | None = None
    type_text: str | None = None
    type_user_selected: bool | None = None
    system: str | None = None
    value: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    assigner: str | None = None
    assigner_display: str | None = None
    assigner_identifier_use: IdentifierUse | None = None
    assigner_identifier_type_system: str | None = None
    assigner_identifier_type_version: str | None = None
    assigner_identifier_type_code: str | None = None
    assigner_identifier_type_display: str | None = None
    assigner_identifier_type_text: str | None = None
    assigner_identifier_type_user_selected: bool | None = None
    assigner_identifier_system: str | None = None
    assigner_identifier_value: str | None = None
    assigner_identifier_period_start: datetime | None = None
    assigner_identifier_period_end: datetime | None = None


class PractitionerQualificationPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identifier: list[QualificationIdentifierPatch] | None = None
    code_system: str | None = None
    code_code: str | None = None
    code_display: str | None = None
    code_text: str | None = None
    status_system: str | None = None
    status_code: str | None = None
    status_display: str | None = None
    status_text: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    issuer: str | None = Field(
        None, description="FHIR reference, e.g. 'Organization/100'."
    )
    issuer_display: str | None = None
    issuer_identifier_use: IdentifierUse | None = None
    issuer_identifier_type_system: str | None = None
    issuer_identifier_type_version: str | None = None
    issuer_identifier_type_code: str | None = None
    issuer_identifier_type_display: str | None = None
    issuer_identifier_type_text: str | None = None
    issuer_identifier_type_user_selected: bool | None = None
    issuer_identifier_system: str | None = None
    issuer_identifier_value: str | None = None
    issuer_identifier_period_start: datetime | None = None
    issuer_identifier_period_end: datetime | None = None


class PractitionerCommunicationPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language_system: str | None = None
    language_version: str | None = None
    language_code: str | None = None
    language_display: str | None = None
    language_text: str | None = None
    language_user_selected: bool | None = None


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
        True, description="Whether this practitioner's record is in active use."
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
