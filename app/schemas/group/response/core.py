from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)
from app.schemas.group.response.characteristic import (
    FHIRGroupCharacteristic,
    PlainGroupCharacteristic,
)
from app.schemas.group.response.codeable_concept import PlainGroupCodeableConcept
from app.schemas.group.response.identifier import PlainGroupIdentifier
from app.schemas.group.response.member import FHIRGroupMember, PlainGroupMember


class FHIRGroupSchema(BaseModel):
    """FHIR R4 Group resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Group"] = "Group"
    id: str
    meta: FHIRMeta | None = None
    identifier: list[FHIRIdentifier] | None = None
    active: bool | None = None
    type: str
    actual: bool
    code: FHIRCodeableConcept | None = None
    name: str | None = None
    quantity: int | None = None
    managingEntity: FHIRReference | None = None
    characteristic: list[FHIRGroupCharacteristic] | None = None
    member: list[FHIRGroupMember] | None = None
    extension: list[dict[str, Any]] | None = None


class PlainGroupResponse(BaseModel):
    """Plain snake_case response schema for Group."""

    model_config = ConfigDict(extra="ignore")

    id: int = Field(..., description="Public sequence Group ID.")
    active: bool | None = Field(None, description="Whether this group's record is in active use.")
    type: str = Field(..., description="person | animal | practitioner | device | medication | substance.")
    actual: bool = Field(..., description="true for actual group, false for definitional.")
    code: PlainGroupCodeableConcept | None = Field(None, description="Kind of Group members.")
    name: str | None = Field(None, description="Label for Group.")
    quantity: int | None = Field(None, description="Number of members in group.")
    managing_entity: str | None = Field(None, description="Entity that is custodian of Group.")
    managing_entity_display: str | None = Field(None, description="Display text for managingEntity.")
    identifier: list[PlainGroupIdentifier] | None = Field(None, description="External identifiers.")
    characteristic: list[PlainGroupCharacteristic] | None = Field(None, description="Characteristics.")
    member: list[PlainGroupMember] | None = Field(None, description="Group members.")
    extension: list[dict[str, Any]] | None = Field(None, description="Extensions.")


class PaginatedGroupResponse(BaseModel):
    """Paginated response for plain Group listing."""

    model_config = ConfigDict(extra="ignore")

    total: int
    limit: int
    offset: int
    data: list[PlainGroupResponse]


class FHIRGroupBundleEntry(BaseModel):
    """Single entry in FHIR Group searchset bundle."""

    model_config = ConfigDict(extra="allow")

    fullUrl: str | None = None
    resource: FHIRGroupSchema


class FHIRGroupBundle(BaseModel):
    """FHIR searchset Bundle for Group resources."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Bundle"] = "Bundle"
    type: Literal["searchset"] = "searchset"
    total: int
    entry: list[FHIRGroupBundleEntry] = []
