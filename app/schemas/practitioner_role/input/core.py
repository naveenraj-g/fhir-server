from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse

from .available_time import PractitionerRoleAvailableTimeInput
from .code import PractitionerRoleCodeInput
from .endpoint import PractitionerRoleEndpointInput
from .healthcare_service import PractitionerRoleHealthcareServiceInput
from .identifier import PractitionerRoleIdentifierInput
from .location import PractitionerRoleLocationInput
from .not_available import PractitionerRoleNotAvailableInput
from .specialty import PractitionerRoleSpecialtyInput
from .telecom import PractitionerRoleTelecomInput


class PractitionerRoleCreateSchema(BaseModel):
    """Creates a PractitionerRole and any combination of its 9 sub-resource
    lists atomically in one request — same set-once-then-patch shape as
    Organization/HealthcareService, no separate scalar-only vs. full create
    split. org_id and created_by both come from the verified JWT (actor.org_id
    / actor.sub) — neither is a request body field. Like Organization,
    Location, and HealthcareService, PractitionerRole has no user_id field at
    all — it's a shared tenant-level entity (which practitioners may act in
    which roles at this org), not scoped to an individual end-user."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "active": True,
                "period_start": "2024-01-01T00:00:00Z",
                "practitioner": "Practitioner/30001",
                "practitioner_display": "Dr. Jane Smith",
                "organization": "Organization/190001",
                "organization_display": "General Hospital",
                "availability_exceptions": "Not available on public holidays",
                "code": [
                    {
                        "coding_system": "http://snomed.info/sct",
                        "coding_code": "59058001",
                        "coding_display": "General physician",
                    }
                ],
                "specialty": [
                    {
                        "coding_system": "http://snomed.info/sct",
                        "coding_code": "394814009",
                        "coding_display": "General practice",
                    }
                ],
                "location": [],
                "healthcare_service": [],
                "telecom": [{"system": "phone", "value": "555-1234", "use": "work"}],
                "available_time": [
                    {
                        "days_of_week": ["mon", "tue", "wed", "thu", "fri"],
                        "available_start_time": "09:00:00",
                        "available_end_time": "17:00:00",
                    }
                ],
                "not_available": [],
                "endpoint": [],
                "identifier": [],
            }
        },
    )

    active: bool | None = Field(
        False, description="Whether this practitioner role record is in active use."
    )

    # period (0..1 Period) — flattened
    period_start: datetime | None = Field(
        None,
        description="Start of the period during which the practitioner is authorized to perform in these role(s).",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period during which the practitioner is authorized to perform in these role(s).",
    )

    # practitioner (0..1) Reference(Practitioner)
    practitioner: str | None = Field(
        None,
        description="Practitioner providing services for the organization, as a FHIR reference string (e.g. 'Practitioner/30001').",
    )
    practitioner_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the practitioner in addition to the reference.",
    )
    practitioner_identifier_use: IdentifierUse | None = Field(
        None,
        description="Logical-identifier fallback for practitioner (used when the practitioner isn't a resource in this system) — identifies the purpose for that identifier, if known.",
    )
    practitioner_identifier_type_system: str | None = Field(
        None,
        description="Fallback identifier — the code system that defines the meaning of its type code.",
    )
    practitioner_identifier_type_version: str | None = Field(
        None,
        description="Fallback identifier — the version of the code system used for its type code.",
    )
    practitioner_identifier_type_code: str | None = Field(
        None,
        description="Fallback identifier — a symbol in syntax defined by the code system.",
    )
    practitioner_identifier_type_display: str | None = Field(
        None,
        description="Fallback identifier — a representation of the meaning of its type code.",
    )
    practitioner_identifier_type_text: str | None = Field(
        None,
        description="Fallback identifier — a human language representation of its type.",
    )
    practitioner_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was chosen by a user directly.",
    )
    practitioner_identifier_system: str | None = Field(
        None, description="Fallback identifier — the namespace URL for the value."
    )
    practitioner_identifier_value: str | None = Field(
        None,
        description="Fallback identifier — the portion typically relevant to the user, unique within the system.",
    )
    practitioner_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of its validity period."
    )
    practitioner_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of its validity period."
    )

    # organization (0..1) Reference(Organization)
    organization: str | None = Field(
        None,
        description="Organization where the roles are available, as a FHIR reference string (e.g. 'Organization/190001').",
    )
    organization_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the organization in addition to the reference.",
    )
    organization_identifier_use: IdentifierUse | None = Field(
        None,
        description="Logical-identifier fallback for organization (used when the organization isn't a resource in this system) — identifies the purpose for that identifier, if known.",
    )
    organization_identifier_type_system: str | None = Field(
        None,
        description="Fallback identifier — the code system that defines the meaning of its type code.",
    )
    organization_identifier_type_version: str | None = Field(
        None,
        description="Fallback identifier — the version of the code system used for its type code.",
    )
    organization_identifier_type_code: str | None = Field(
        None,
        description="Fallback identifier — a symbol in syntax defined by the code system.",
    )
    organization_identifier_type_display: str | None = Field(
        None,
        description="Fallback identifier — a representation of the meaning of its type code.",
    )
    organization_identifier_type_text: str | None = Field(
        None,
        description="Fallback identifier — a human language representation of its type.",
    )
    organization_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was chosen by a user directly.",
    )
    organization_identifier_system: str | None = Field(
        None, description="Fallback identifier — the namespace URL for the value."
    )
    organization_identifier_value: str | None = Field(
        None,
        description="Fallback identifier — the portion typically relevant to the user, unique within the system.",
    )
    organization_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of its validity period."
    )
    organization_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of its validity period."
    )

    availability_exceptions: str | None = Field(
        None,
        description="A description of site availability exceptions, e.g. public holiday availability.",
    )

    identifier: list[PractitionerRoleIdentifierInput] | None = Field(
        None, description="Business identifiers that are specific to a role/location."
    )
    code: list[PractitionerRoleCodeInput] | None = Field(
        None, description="Roles which this practitioner may perform."
    )
    specialty: list[PractitionerRoleSpecialtyInput] | None = Field(
        None, description="Specific expertise of the practitioner."
    )
    location: list[PractitionerRoleLocationInput] | None = Field(
        None, description="The location(s) at which this practitioner provides care."
    )
    healthcare_service: list[PractitionerRoleHealthcareServiceInput] | None = Field(
        None, description="Healthcare services provided at this role/location."
    )
    telecom: list[PractitionerRoleTelecomInput] | None = Field(
        None, description="Contact details that are specific to the role/location/service."
    )
    available_time: list[PractitionerRoleAvailableTimeInput] | None = Field(
        None, description="A collection of times the role is available."
    )
    not_available: list[PractitionerRoleNotAvailableInput] | None = Field(
        None,
        description="This role is not available during this period of time due to the provided reason.",
    )
    endpoint: list[PractitionerRoleEndpointInput] | None = Field(
        None,
        description="Technical endpoints providing access to services operated for this role.",
    )


class PractitionerRolePatchSchema(BaseModel):
    """Partial update — only supplied fields are written. Every supplied
    sub-resource list (even `[]`) replaces the corresponding rows wholesale;
    omitted lists are left untouched. updated_by comes from the verified
    JWT (actor.sub), not a request body field."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "active": True,
                "telecom": [{"system": "phone", "value": "555-1234", "use": "work"}],
            }
        },
    )

    active: bool | None = Field(
        None, description="Whether this practitioner role record is in active use."
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the period during which the practitioner is authorized to perform in these role(s).",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the period during which the practitioner is authorized to perform in these role(s).",
    )

    practitioner: str | None = Field(
        None,
        description="Practitioner providing services for the organization, as a FHIR reference string (e.g. 'Practitioner/30001'). Set to null to clear.",
    )
    practitioner_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the practitioner in addition to the reference.",
    )
    practitioner_identifier_use: IdentifierUse | None = Field(
        None,
        description="Logical-identifier fallback for practitioner — identifies the purpose for that identifier, if known.",
    )
    practitioner_identifier_type_system: str | None = Field(
        None,
        description="Fallback identifier — the code system that defines the meaning of its type code.",
    )
    practitioner_identifier_type_version: str | None = Field(
        None,
        description="Fallback identifier — the version of the code system used for its type code.",
    )
    practitioner_identifier_type_code: str | None = Field(
        None,
        description="Fallback identifier — a symbol in syntax defined by the code system.",
    )
    practitioner_identifier_type_display: str | None = Field(
        None,
        description="Fallback identifier — a representation of the meaning of its type code.",
    )
    practitioner_identifier_type_text: str | None = Field(
        None,
        description="Fallback identifier — a human language representation of its type.",
    )
    practitioner_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was chosen by a user directly.",
    )
    practitioner_identifier_system: str | None = Field(
        None, description="Fallback identifier — the namespace URL for the value."
    )
    practitioner_identifier_value: str | None = Field(
        None,
        description="Fallback identifier — the portion typically relevant to the user, unique within the system.",
    )
    practitioner_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of its validity period."
    )
    practitioner_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of its validity period."
    )

    organization: str | None = Field(
        None,
        description="Organization where the roles are available, as a FHIR reference string (e.g. 'Organization/190001'). Set to null to clear.",
    )
    organization_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the organization in addition to the reference.",
    )
    organization_identifier_use: IdentifierUse | None = Field(
        None,
        description="Logical-identifier fallback for organization — identifies the purpose for that identifier, if known.",
    )
    organization_identifier_type_system: str | None = Field(
        None,
        description="Fallback identifier — the code system that defines the meaning of its type code.",
    )
    organization_identifier_type_version: str | None = Field(
        None,
        description="Fallback identifier — the version of the code system used for its type code.",
    )
    organization_identifier_type_code: str | None = Field(
        None,
        description="Fallback identifier — a symbol in syntax defined by the code system.",
    )
    organization_identifier_type_display: str | None = Field(
        None,
        description="Fallback identifier — a representation of the meaning of its type code.",
    )
    organization_identifier_type_text: str | None = Field(
        None,
        description="Fallback identifier — a human language representation of its type.",
    )
    organization_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was chosen by a user directly.",
    )
    organization_identifier_system: str | None = Field(
        None, description="Fallback identifier — the namespace URL for the value."
    )
    organization_identifier_value: str | None = Field(
        None,
        description="Fallback identifier — the portion typically relevant to the user, unique within the system.",
    )
    organization_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of its validity period."
    )
    organization_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of its validity period."
    )

    availability_exceptions: str | None = Field(
        None, description="A description of site availability exceptions."
    )

    identifier: list[PractitionerRoleIdentifierInput] | None = Field(
        None, description="Business identifiers — replaces the full list if supplied."
    )
    code: list[PractitionerRoleCodeInput] | None = Field(
        None, description="Roles which this practitioner may perform — replaces the full list if supplied."
    )
    specialty: list[PractitionerRoleSpecialtyInput] | None = Field(
        None, description="Specialties — replaces the full list if supplied."
    )
    location: list[PractitionerRoleLocationInput] | None = Field(
        None,
        description="Location(s) at which this practitioner provides care — replaces the full list if supplied.",
    )
    healthcare_service: list[PractitionerRoleHealthcareServiceInput] | None = Field(
        None,
        description="Healthcare service(s) — replaces the full list if supplied.",
    )
    telecom: list[PractitionerRoleTelecomInput] | None = Field(
        None, description="Contact detail(s) — replaces the full list if supplied."
    )
    available_time: list[PractitionerRoleAvailableTimeInput] | None = Field(
        None,
        description="Available time window(s) — replaces the full list if supplied.",
    )
    not_available: list[PractitionerRoleNotAvailableInput] | None = Field(
        None,
        description="Not-available period(s) — replaces the full list if supplied.",
    )
    endpoint: list[PractitionerRoleEndpointInput] | None = Field(
        None, description="Technical endpoint(s) — replaces the full list if supplied."
    )
