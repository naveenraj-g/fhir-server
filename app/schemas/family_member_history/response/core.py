from datetime import date as py_date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.family_member_history.response.codeable_concept import (
    PlainFamilyMemberHistoryCodeableConcept,
)
from app.schemas.family_member_history.response.condition import (
    FHIRFamilyMemberHistoryCondition,
    PlainFamilyMemberHistoryCondition,
)
from app.schemas.family_member_history.response.identifier import (
    PlainFamilyMemberHistoryIdentifier,
)
from app.schemas.family_member_history.response.note import (
    PlainFamilyMemberHistoryNote,
)
from app.schemas.family_member_history.response.reason_code import (
    PlainFamilyMemberHistoryReasonCode,
)
from app.schemas.family_member_history.response.reason_reference import (
    PlainFamilyMemberHistoryReasonReference,
)


class FHIRFamilyMemberHistorySchema(BaseModel):
    """FHIR R4 FamilyMemberHistory resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["FamilyMemberHistory"] = "FamilyMemberHistory"
    id: str
    meta: FHIRMeta | None = None
    identifier: list[FHIRIdentifier] | None = None
    instantiatesCanonical: list[str] | None = None
    instantiatesUri: list[str] | None = None
    status: str
    dataAbsentReason: FHIRCodeableConcept | None = None
    patient: FHIRReference
    date: str | None = None
    name: str | None = None
    relationship: FHIRCodeableConcept
    sex: FHIRCodeableConcept | None = None

    bornPeriod: FHIRPeriod | None = None
    bornDate: str | None = None
    bornString: str | None = None

    ageAge: dict[str, Any] | None = None
    ageRange: dict[str, Any] | None = None
    ageString: str | None = None
    estimatedAge: bool | None = None

    deceasedBoolean: bool | None = None
    deceasedAge: dict[str, Any] | None = None
    deceasedRange: dict[str, Any] | None = None
    deceasedDate: str | None = None
    deceasedString: str | None = None

    reasonCode: list[FHIRCodeableConcept] | None = None
    reasonReference: list[FHIRReference] | None = None
    note: list[dict[str, Any]] | None = None
    condition: list[FHIRFamilyMemberHistoryCondition] | None = None
    extension: list[dict[str, Any]] | None = None


class PlainFamilyMemberHistoryResponse(BaseModel):
    """Plain snake_case response schema for FamilyMemberHistory."""

    model_config = ConfigDict(extra="ignore")

    id: int = Field(..., description="Public sequence FamilyMemberHistory ID.")
    status: str = Field(..., description="partial | completed | entered-in-error | health-unknown.")
    data_absent_reason: PlainFamilyMemberHistoryCodeableConcept | None = None

    patient: str = Field(..., description="Patient history is about.")
    patient_display: str | None = None
    patient_identifier_use: str | None = None
    patient_identifier_type_system: str | None = None
    patient_identifier_type_version: str | None = None
    patient_identifier_type_code: str | None = None
    patient_identifier_type_display: str | None = None
    patient_identifier_type_user_selected: bool | None = None
    patient_identifier_type_text: str | None = None
    patient_identifier_system: str | None = None
    patient_identifier_value: str | None = None
    patient_identifier_period_start: str | None = None
    patient_identifier_period_end: str | None = None

    date: datetime | None = None
    name: str | None = None
    relationship: PlainFamilyMemberHistoryCodeableConcept = Field(
        ..., description="Relationship to the subject."
    )
    sex: PlainFamilyMemberHistoryCodeableConcept | None = None

    born_period_start: datetime | None = None
    born_period_end: datetime | None = None
    born_date: py_date | None = None
    born_string: str | None = None

    age_age_value: float | None = None
    age_age_comparator: str | None = None
    age_age_unit: str | None = None
    age_age_system: str | None = None
    age_age_code: str | None = None

    age_range_low_value: float | None = None
    age_range_low_unit: str | None = None
    age_range_low_system: str | None = None
    age_range_low_code: str | None = None
    age_range_high_value: float | None = None
    age_range_high_unit: str | None = None
    age_range_high_system: str | None = None
    age_range_high_code: str | None = None

    age_string: str | None = None
    estimated_age: bool | None = None

    deceased_boolean: bool | None = None
    deceased_age_value: float | None = None
    deceased_age_comparator: str | None = None
    deceased_age_unit: str | None = None
    deceased_age_system: str | None = None
    deceased_age_code: str | None = None

    deceased_range_low_value: float | None = None
    deceased_range_low_unit: str | None = None
    deceased_range_low_system: str | None = None
    deceased_range_low_code: str | None = None
    deceased_range_high_value: float | None = None
    deceased_range_high_unit: str | None = None
    deceased_range_high_system: str | None = None
    deceased_range_high_code: str | None = None

    deceased_date: py_date | None = None
    deceased_string: str | None = None

    instantiates_canonical: list[str] | None = None
    instantiates_uri: list[str] | None = None

    identifier: list[PlainFamilyMemberHistoryIdentifier] | None = None
    reason_code: list[PlainFamilyMemberHistoryReasonCode] | None = None
    reason_reference: list[PlainFamilyMemberHistoryReasonReference] | None = None
    note: list[PlainFamilyMemberHistoryNote] | None = None
    condition: list[PlainFamilyMemberHistoryCondition] | None = None
    extension: list[dict[str, Any]] | None = None

    created_at: datetime | None = Field(None, description="Timestamp of resource creation.")
    updated_at: datetime | None = Field(None, description="Timestamp of resource update.")


class PaginatedFamilyMemberHistoryResponse(BaseModel):
    """Paginated response for plain FamilyMemberHistory listing."""

    model_config = ConfigDict(extra="ignore")

    total: int
    limit: int
    offset: int
    data: list[PlainFamilyMemberHistoryResponse]


class FHIRFamilyMemberHistoryBundleEntry(BaseModel):
    """Single entry in FHIR FamilyMemberHistory searchset bundle."""

    model_config = ConfigDict(extra="allow")

    fullUrl: str | None = None
    resource: FHIRFamilyMemberHistorySchema


class FHIRFamilyMemberHistoryBundle(BaseModel):
    """FHIR searchset Bundle for FamilyMemberHistory resources."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Bundle"] = "Bundle"
    type: Literal["searchset"] = "searchset"
    total: int
    entry: list[FHIRFamilyMemberHistoryBundleEntry] = []
