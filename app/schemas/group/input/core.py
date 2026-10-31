from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.group.enums import GroupType
from app.schemas.group.input.characteristic import GroupCharacteristicInput
from app.schemas.group.input.codeable_concept import GroupCodeableConceptInput
from app.schemas.group.input.identifier import GroupIdentifierInput
from app.schemas.group.input.member import GroupMemberInput


class GroupCreateSchema(BaseModel):
    """Schema for creating a Group resource (POST /api/fhir/v1/groups)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "type": "person",
                "actual": True,
                "active": True,
                "name": "Diabetes Support Group",
                "quantity": 2,
                "code": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "394582007",
                            "display": "Community health",
                        }
                    ],
                    "text": "Community health",
                },
                "managing_entity": "Organization/190001",
                "managing_entity_display": "Primary Care Clinic",
                "identifier": [
                    {
                        "use": "official",
                        "system": "http://example.org/groups",
                        "value": "GRP-001",
                    }
                ],
                "characteristic": [
                    {
                        "code": {
                            "coding": [
                                {
                                    "system": "http://snomed.info/sct",
                                    "code": "73211009",
                                    "display": "Diabetes mellitus",
                                }
                            ],
                            "text": "Diabetes mellitus",
                        },
                        "value_boolean": True,
                        "exclude": False,
                    }
                ],
                "member": [
                    {
                        "entity": "Patient/10001",
                        "entity_display": "John Doe",
                        "inactive": False,
                    }
                ],
            }
        },
    )

    active: bool | None = Field(
        None, description="Whether this group's record is in active use."
    )
    type: GroupType = Field(
        ...,
        description="person | animal | practitioner | device | medication | substance.",
    )
    actual: bool = Field(
        ...,
        description="true for actual specific group, false for definitional.",
    )
    code: GroupCodeableConceptInput | None = Field(
        None, description="Kind of Group members."
    )
    name: str | None = Field(
        None, description="Label for Group."
    )
    quantity: int | None = Field(
        None, ge=0, description="Number of members in group."
    )
    managing_entity: str | None = Field(
        None, description="Entity that is the custodian of the Group's info (Organization | RelatedPerson | Practitioner | PractitionerRole)."
    )
    managing_entity_display: str | None = Field(
        None, description="Plain text display for managingEntity."
    )
    identifier: list[GroupIdentifierInput] | None = Field(
        None, description="External identifiers for this group."
    )
    characteristic: list[GroupCharacteristicInput] | None = Field(
        None, description="Include / Exclude group members by characteristic."
    )
    member: list[GroupMemberInput] | None = Field(
        None, description="Who or what is in group."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="May be used to represent additional information not part of the basic definition."
    )


class GroupPatchSchema(BaseModel):
    """Schema for updating a Group resource (PATCH /api/fhir/v1/groups/{id})."""

    model_config = ConfigDict(extra="forbid")

    active: bool | None = Field(
        None, description="Whether this group's record is in active use."
    )
    type: GroupType | None = Field(
        None,
        description="person | animal | practitioner | device | medication | substance.",
    )
    actual: bool | None = Field(
        None,
        description="true for actual specific group, false for definitional.",
    )
    code: GroupCodeableConceptInput | None = Field(
        None, description="Kind of Group members."
    )
    name: str | None = Field(
        None, description="Label for Group."
    )
    quantity: int | None = Field(
        None, ge=0, description="Number of members in group."
    )
    managing_entity: str | None = Field(
        None, description="Entity that is the custodian of the Group's info."
    )
    managing_entity_display: str | None = Field(
        None, description="Plain text display for managingEntity."
    )
    identifier: list[GroupIdentifierInput] | None = Field(
        None, description="External identifiers for this group."
    )
    characteristic: list[GroupCharacteristicInput] | None = Field(
        None, description="Include / Exclude group members by characteristic."
    )
    member: list[GroupMemberInput] | None = Field(
        None, description="Who or what is in group."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="May be used to represent additional information not part of the basic definition."
    )
