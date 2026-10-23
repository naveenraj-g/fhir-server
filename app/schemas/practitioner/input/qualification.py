from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput
from app.schemas.enums import IdentifierUse


class PractitionerQualificationIdentifierInput(BaseModel):
    """Practitioner.qualification.identifier — identifiers for this
    qualification (Identifier). Same shape as PractitionerIdentifierInput —
    see that file's docstring for the coding/assigner-fallback reasoning."""

    model_config = ConfigDict(extra="forbid")
    use: IdentifierUse | None = Field(
        None,
        description="Identifies the purpose for this identifier, if known — usual|official|temp|secondary|old.",
    )
    type_coding: list[CodingInput] | None = Field(
        None, description="Coding(s) for this identifier's type."
    )
    type_text: str | None = Field(
        None,
        description="A human language representation of the identifier's type, as seen/selected/entered by the user.",
    )
    system: str | None = Field(
        None,
        description="Establishes the namespace for the value — that is, a URL that describes a set of unique values.",
    )
    value: str | None = Field(
        None,
        description="The portion of the identifier typically relevant to the user and which is unique within the context of the system.",
    )
    period_start: datetime | None = Field(
        None,
        description="Start of the time period during which this identifier is/was valid for use.",
    )
    period_end: datetime | None = Field(
        None,
        description="End of the time period during which this identifier is/was valid for use.",
    )
    assigner: str | None = Field(
        None,
        description="Organization that issued/manages this identifier, as a FHIR reference string (e.g. 'Organization/190001').",
    )
    assigner_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the assigning organization in addition to the reference.",
    )
    assigner_identifier_use: IdentifierUse | None = Field(
        None,
        description="Logical-identifier fallback for the assigner — identifies the purpose for that identifier, if known.",
    )
    assigner_identifier_type_system: str | None = Field(
        None,
        description="Fallback identifier — the code system that defines the meaning of its type code.",
    )
    assigner_identifier_type_version: str | None = Field(
        None,
        description="Fallback identifier — the version of the code system used for its type code.",
    )
    assigner_identifier_type_code: str | None = Field(
        None,
        description="Fallback identifier — a symbol in syntax defined by the code system.",
    )
    assigner_identifier_type_display: str | None = Field(
        None,
        description="Fallback identifier — a representation of the meaning of its type code.",
    )
    assigner_identifier_type_text: str | None = Field(
        None,
        description="Fallback identifier — a human language representation of its type.",
    )
    assigner_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was chosen by a user directly.",
    )
    assigner_identifier_system: str | None = Field(
        None, description="Fallback identifier — the namespace URL for the value."
    )
    assigner_identifier_value: str | None = Field(
        None,
        description="Fallback identifier — the portion typically relevant to the user, unique within the system.",
    )
    assigner_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of its validity period."
    )
    assigner_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of its validity period."
    )


class PractitionerQualificationInput(BaseModel):
    """Practitioner.qualification — certifications, licenses, or training
    (BackboneElement). `code` is 1..1 (REQUIRED by spec) — enforced here by
    making `code_coding`/`code_text` a required pair at the application
    layer isn't practical since either alone can satisfy a CodeableConcept,
    so neither is Pydantic-required; the FHIR validator layer is what
    actually enforces code's presence, same architecture choice as every
    other cross-field R4 rule in this project (see OrganizationModel's
    docstring, app/models/organization/core.py)."""

    model_config = ConfigDict(extra="forbid")
    identifier: list[PractitionerQualificationIdentifierInput] | None = Field(
        None, description="Identifier(s) for this qualification."
    )
    code_coding: list[CodingInput] | None = Field(
        None,
        description="Coding(s) for this qualification — e.g. a v2 table 0360 qualification code.",
    )
    code_text: str | None = Field(
        None,
        description="A human language representation of the qualification code.",
    )
    period_start: datetime | None = Field(
        None, description="Start of the period during which the qualification is valid."
    )
    period_end: datetime | None = Field(
        None, description="End of the period during which the qualification is valid."
    )
    issuer: str | None = Field(
        None,
        description="Organization that regulates and issues the qualification, as a FHIR reference string (e.g. 'Organization/190001').",
    )
    issuer_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the issuing organization in addition to the reference.",
    )
    issuer_identifier_use: IdentifierUse | None = Field(
        None,
        description="Logical-identifier fallback for the issuer (used when it isn't a resource in this system) — identifies the purpose for that identifier, if known.",
    )
    issuer_identifier_type_system: str | None = Field(
        None,
        description="Fallback identifier — the code system that defines the meaning of its type code.",
    )
    issuer_identifier_type_version: str | None = Field(
        None,
        description="Fallback identifier — the version of the code system used for its type code.",
    )
    issuer_identifier_type_code: str | None = Field(
        None,
        description="Fallback identifier — a symbol in syntax defined by the code system.",
    )
    issuer_identifier_type_display: str | None = Field(
        None,
        description="Fallback identifier — a representation of the meaning of its type code.",
    )
    issuer_identifier_type_text: str | None = Field(
        None,
        description="Fallback identifier — a human language representation of its type.",
    )
    issuer_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was chosen by a user directly.",
    )
    issuer_identifier_system: str | None = Field(
        None, description="Fallback identifier — the namespace URL for the value."
    )
    issuer_identifier_value: str | None = Field(
        None,
        description="Fallback identifier — the portion typically relevant to the user, unique within the system.",
    )
    issuer_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of its validity period."
    )
    issuer_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of its validity period."
    )
